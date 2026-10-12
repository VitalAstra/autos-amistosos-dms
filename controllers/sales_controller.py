"""Operaciones de venta mediante transacciones SQLAlchemy ORM."""

from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re

from sqlalchemy import func, select

from config.database import SessionLocal
from models.customer import Customer
from models.employee import Employee
from models.sales_invoice import SalesInvoice
from models.sales_addons import (
	Customization,
	Financing,
	Insurance,
	TradeIn,
	Warranty,
)
from models.vehicle import Vehicle


class SalesController:
	"""Registra ventas y actualiza el inventario atómicamente."""

	_CENT = Decimal("0.01")

	def process_sale(
		self,
		customer_id: int,
		vehicle_id: str,
		negotiated_price: Decimal | str | int | float,
		tax_rate: Decimal | str | int | float,
		employee_id: int,
		current_mileage: int,
		license_fee: Decimal | str | int | float = 0,
		addons: dict | None = None,
		manager_approval: bool | None = None,
	) -> tuple[bool, str]:
		"""Registra una venta con sus complementos dentro de una transacción.

		``tax_rate`` se expresa como fracción: por ejemplo, ``Decimal("0.13")``
		representa un impuesto del 13 por ciento. El empleado es obligatorio
		para guardar la referencia exigida por la factura. La disponibilidad
		se determina por la ausencia de una factura para el VIN, según el esquema
		actual de PostgreSQL.
		"""
		try:
			price = self._to_nonnegative_decimal(negotiated_price, "El precio")
			rate = self._to_nonnegative_decimal(tax_rate, "La tasa de impuestos")
			if rate > 1:
				raise ValueError("La tasa de impuestos debe estar entre 0 y 1.")
			plate_cost = self._to_nonnegative_decimal(license_fee, "El costo de placas")
			addon_data = self._validate_addons(addons or {})
			additional_cost = (
				addon_data["warranty"].get("extended_cost", Decimal("0"))
				if addon_data["warranty"]
				else Decimal("0")
			) + (
				addon_data["customization"].get("cost", Decimal("0"))
				if addon_data["customization"]
				else Decimal("0")
			)
			trade_in_allowance = (
				addon_data["trade_in"].get("allowance", Decimal("0"))
				if addon_data["trade_in"]
				else Decimal("0")
			)
			taxable_subtotal = price + additional_cost - trade_in_allowance
			if taxable_subtotal < 0:
				raise ValueError("El subtotal de la venta no puede ser negativo.")
			tax_amount = (taxable_subtotal * rate).quantize(
				self._CENT, rounding=ROUND_HALF_UP
			)
			total_amount = taxable_subtotal + tax_amount + plate_cost
			if not isinstance(current_mileage, int) or current_mileage < 0:
				raise ValueError("El kilometraje debe ser un entero no negativo.")

			with SessionLocal() as session:
				try:
					vehicle = session.scalars(
						select(Vehicle)
						.where(Vehicle.id == vehicle_id)
						.where(~Vehicle.sales_invoices.any())
						.with_for_update()
					).one_or_none()
					if vehicle is None:
						raise ValueError(
							"El vehículo no existe o ya tiene una factura asociada."
						)
					if session.get(Customer, customer_id) is None:
						raise ValueError("No se encontró el cliente seleccionado.")
					if session.get(Employee, employee_id) is None:
						raise ValueError("No se encontró el empleado seleccionado.")

					invoice = SalesInvoice(
						customer_id=customer_id,
						vehicle_id=vehicle.id,
						employee_id=employee_id,
						current_mileage=current_mileage,
						negotiated_price=price,
						manager_approval=manager_approval,
						tax_amount=tax_amount,
						license_fee_amount=plate_cost,
						total_amount=total_amount,
					)
					session.add(invoice)
					if addon_data["trade_in"]:
						invoice.trade_in = TradeIn(**addon_data["trade_in"])
					if addon_data["financing"]:
						invoice.financing = Financing(**addon_data["financing"])
					if addon_data["insurance"]:
						invoice.insurance = Insurance(**addon_data["insurance"])
					if addon_data["warranty"]:
						invoice.warranty = Warranty(**addon_data["warranty"])
					if addon_data["customization"]:
						invoice.customization = Customization(
							**addon_data["customization"]
						)
					session.commit()
					invoice_id = invoice.id
				except Exception:
					session.rollback()
					raise

			return True, f"Venta registrada con factura {invoice_id}."
		except Exception as error:
			return False, str(error)

	def get_dashboard_data(self) -> dict[str, int | str]:
		"""Consulta métricas actuales para el panel principal."""
		today = date.today()
		month_start = today.replace(day=1)
		with SessionLocal() as session:
			available_vehicles = session.scalar(
				select(func.count())
				.select_from(Vehicle)
				.where(~Vehicle.sales_invoices.any())
			)
			monthly_sales = session.scalar(
				select(func.count())
				.select_from(SalesInvoice)
				.where(SalesInvoice.date >= month_start, SalesInvoice.date <= today)
			)
			new_prospects = session.scalar(
				select(func.count())
				.select_from(Customer)
				.where(Customer.status_type == "Potential")
			)
			revenue = session.scalar(
				select(func.coalesce(func.sum(SalesInvoice.total_amount), 0)).where(
					SalesInvoice.date >= month_start, SalesInvoice.date <= today
				)
			)
		return {
			"vehicles_available": available_vehicles or 0,
			"monthly_sales": monthly_sales or 0,
			"new_prospects": new_prospects or 0,
			"invoiced_revenue": f"${Decimal(str(revenue or 0)):,.2f}",
		}

	def get_recent_sales(self, limit: int = 5) -> list[dict[str, object]]:
		"""Obtiene las facturas recientes como filas listas para el dashboard."""
		if limit < 1:
			raise ValueError("El límite debe ser mayor que cero.")
		with SessionLocal() as session:
			rows = session.execute(
				select(SalesInvoice, Customer, Vehicle)
				.join(SalesInvoice.customer)
				.join(SalesInvoice.vehicle)
				.order_by(SalesInvoice.date.desc(), SalesInvoice.id.desc())
				.limit(limit)
			).all()
		return [
			{
				"Factura": invoice.id,
				"Cliente": f"{customer.first_name} {customer.last_name}".strip(),
				"Vehículo": " ".join(
					part
					for part in (vehicle.manufacturer, vehicle.model)
					if part
				),
				"Monto": f"${invoice.total_amount:,.2f}",
				"Fecha": invoice.date.isoformat(),
			}
			for invoice, customer, vehicle in rows
		]

	def get_sales_history(self) -> list[dict[str, object]]:
		"""Retorna facturas con sus clientes, vehículos y empleados relacionados."""
		with SessionLocal() as session:
			rows = session.execute(
				select(SalesInvoice, Customer, Vehicle, Employee)
				.join(SalesInvoice.customer)
				.join(SalesInvoice.vehicle)
				.join(SalesInvoice.employee)
				.order_by(SalesInvoice.date.desc(), SalesInvoice.id.desc())
			).all()

		return [
			{
				"invoice_number": invoice.id,
				"date": invoice.date,
				"customer_name": f"{customer.first_name} {customer.last_name}".strip(),
				"vehicle_id": vehicle.id,
				"vehicle": " ".join(
					part
					for part in (vehicle.manufacturer, vehicle.model)
					if part
				),
				"employee_name": (
					f"{employee.first_name} {employee.last_name}".strip()
				),
				"negotiated_price": invoice.negotiated_price,
				"tax_amount": invoice.tax_amount,
				"license_fee_amount": invoice.license_fee_amount,
				"total_amount": invoice.total_amount,
			}
			for invoice, customer, vehicle, employee in rows
		]

	@classmethod
	def _validate_addons(cls, addons: dict) -> dict[str, dict | None]:
		if not isinstance(addons, dict):
			raise ValueError("Los datos de adicionales deben ser un diccionario.")

		specifications = {
			"trade_in": {
				"required": {"old_vehicle_id"},
				"money": {"allowance"},
			},
			"financing": {
				"required": {"source"},
				"money": set(),
			},
			"insurance": {
				"required": {"company", "policy_number"},
				"money": set(),
			},
			"warranty": {
				"required": {"type"},
				"money": {"extended_cost"},
			},
			"customization": {
				"required": {"type"},
				"money": {"cost"},
			},
		}
		normalized: dict[str, dict | None] = {}
		for name, specification in specifications.items():
			values = addons.get(name)
			if values is None:
				normalized[name] = None
				continue
			if not isinstance(values, dict):
				raise ValueError(f"Los datos de {name} deben ser un diccionario.")
			data = dict(values)
			missing_fields = specification["required"] - data.keys()
			if missing_fields:
				missing = ", ".join(sorted(missing_fields))
				raise ValueError(f"Faltan campos de {name}: {missing}.")
			for field in specification["money"]:
				if field in data:
					data[field] = cls._to_nonnegative_decimal(
						data[field], f"El importe de {name}"
					)
			if name == "trade_in":
				vin = data["old_vehicle_id"]
				if not isinstance(vin, str) or not re.fullmatch(
					r"[A-HJ-NPR-Z0-9]{17}", vin.strip().upper()
				):
					raise ValueError(
						"El VIN del Trade-In debe tener 17 caracteres "
						"alfanuméricos y no puede incluir I, O ni Q."
					)
				data["old_vehicle_id"] = vin.strip().upper()
			if name == "insurance":
				data["proof_submitted"] = bool(data.get("proof_submitted", False))
			normalized[name] = data
		return normalized

	@classmethod
	def _to_nonnegative_decimal(cls, value, label: str) -> Decimal:
		try:
			amount = Decimal(str(value))
		except (InvalidOperation, TypeError, ValueError) as error:
			raise ValueError(f"{label} debe ser un número válido.") from error
		if not amount.is_finite() or amount < 0:
			raise ValueError(f"{label} debe ser un monto no negativo.")
		return amount.quantize(cls._CENT, rounding=ROUND_HALF_UP)
