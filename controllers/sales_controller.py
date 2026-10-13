"""Operaciones transaccionales y ciclo de aprobación de ventas."""

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from config.database import SessionLocal
from models.customer import Customer
from models.employee import Employee
from models.sales_addons import Customization, Financing, Insurance, TradeIn, Warranty
from models.sales_invoice import SalesInvoice
from models.vehicle import Vehicle
from utils.sales_calculator import calculate_sale_totals


class SalesController:
	"""Registra ventas, comprueba disponibilidad y procesa aprobaciones."""

	_CENT = Decimal("0.01")
	_VIN_PATTERN = re.compile(r"[A-HJ-NPR-Z0-9]{17}")
	_ACTIVE_STATUSES = ("pending", "approved", "completed")

	def process_sale(self, sale_data: dict) -> tuple[bool, str]:
		"""Registra factura y complementos como pendientes de aprobación."""
		if not isinstance(sale_data, dict):
			return False, "Los datos de la venta no son válidos."
		addons = sale_data.get("addons") or {}
		if not isinstance(addons, dict):
			return False, "Los datos de complementos no son válidos."

		try:
			price = self._to_nonnegative_decimal(
				sale_data.get("sales_negotiated_price"), "El precio negociado"
			)
			if price <= 0:
				raise ValueError("El precio negociado debe ser mayor a cero.")
			license_fee = self._to_nonnegative_decimal(
				sale_data.get("sales_license_fee_amount", 0), "La tarifa de placas"
			)
			addon_data = self._validate_addons(addons)
			_, tax_amount, total_amount = calculate_sale_totals(
				price, license_fee, addon_data
			)
			customer_id = int(sale_data["customer_id"])
			employee_id = int(sale_data["employee_id"])
			current_mileage = int(sale_data["sales_current_mileage"])
			vehicle_id = str(sale_data["vehicle_id"]).strip().upper()
			if current_mileage < 0:
				raise ValueError("El kilometraje no puede ser negativo.")
			if not self._VIN_PATTERN.fullmatch(vehicle_id):
				raise ValueError(
					"El VIN debe tener 17 caracteres alfanuméricos "
					"y no puede incluir I, O ni Q."
				)

			with SessionLocal() as session:
				vehicle = session.scalars(
					select(Vehicle)
					.where(Vehicle.id == vehicle_id)
					.where(
						~Vehicle.sales_invoices.any(
							SalesInvoice.status.in_(self._ACTIVE_STATUSES)
						)
					)
					.with_for_update()
				).one_or_none()
				if vehicle is None:
					raise ValueError(
						"El vehículo no existe o ya tiene una venta activa."
					)
				if session.get(Customer, customer_id) is None:
					raise ValueError("No se encontró el cliente seleccionado.")
				employee = session.get(Employee, employee_id)
				if employee is None or not employee.is_active:
					raise ValueError("El vendedor no existe o está inactivo.")
				if employee.role.casefold() != "salesperson":
					raise ValueError("La venta debe registrarse con un vendedor.")

				invoice = SalesInvoice(
					customer_id=customer_id,
					vehicle_id=vehicle.id,
					employee_id=employee_id,
					current_mileage=current_mileage,
					negotiated_price=price,
					manager_approval=None,
					tax_amount=tax_amount,
					license_fee_amount=license_fee,
					total_amount=total_amount,
					status="pending",
				)
				session.add(invoice)
				session.flush()
				self._add_sale_addons(invoice, addon_data)
				session.commit()
				invoice_id = invoice.id

			return True, f"Venta {invoice_id} enviada a aprobación del supervisor."
		except (KeyError, TypeError, ValueError, InvalidOperation) as error:
			return False, str(error)
		except Exception as error:
			return False, f"No se pudo registrar la venta: {error}"

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

	def list_reviewable_sales(self) -> list[SalesInvoice]:
		"""Lista ventas pendientes y aprobadas para supervisión."""
		with SessionLocal() as session:
			return session.scalars(
				select(SalesInvoice)
				.options(
					joinedload(SalesInvoice.customer),
					joinedload(SalesInvoice.vehicle),
					joinedload(SalesInvoice.employee),
				)
				.where(SalesInvoice.status.in_(("pending", "approved")))
				.order_by(SalesInvoice.date, SalesInvoice.id)
			).all()

	def list_pending_sales(self) -> list[SalesInvoice]:
		"""Alias compatible: incluye aprobadas para permitir su cancelación."""
		return self.list_reviewable_sales()

	def approve_sale(self, invoice_id: int, supervisor_id: int) -> tuple[bool, str]:
		return self._review_sale(invoice_id, supervisor_id, "approved")

	def reject_sale(
		self, invoice_id: int, supervisor_id: int, reason: str
	) -> tuple[bool, str]:
		if not isinstance(reason, str) or not reason.strip():
			return False, "El motivo de rechazo es obligatorio."
		return self._review_sale(
			invoice_id, supervisor_id, "rejected", reason.strip()
		)

	def cancel_sale(
		self, invoice_id: int, supervisor_id: int, reason: str
	) -> tuple[bool, str]:
		if not isinstance(reason, str) or not reason.strip():
			return False, "El motivo de cancelación es obligatorio."
		return self._review_sale(
			invoice_id, supervisor_id, "cancelled", reason.strip()
		)

	def _review_sale(
		self, invoice_id: int, supervisor_id: int, decision: str, reason=None
	) -> tuple[bool, str]:
		try:
			with SessionLocal() as session:
				invoice = session.scalars(
					select(SalesInvoice)
					.where(SalesInvoice.id == invoice_id)
					.with_for_update()
				).one_or_none()
				if invoice is None:
					return False, "No se encontró la factura."
				supervisor = session.get(Employee, supervisor_id)
				if (
					supervisor is None
					or not supervisor.is_active
					or supervisor.role.casefold() not in {"manager", "administrator"}
				):
					return False, "Se requiere un supervisor activo para esta acción."

				now = datetime.now(timezone.utc)
				if decision in {"approved", "rejected"}:
					if invoice.status != "pending":
						return False, "La factura ya no está pendiente de aprobación."
					if decision == "approved":
						invoice.manager_approval = True
						invoice.approved_by_employee_id = supervisor_id
						invoice.approved_at = now
						invoice.rejected_by_employee_id = None
						invoice.rejected_at = None
						invoice.rejection_reason = None
					else:
						invoice.manager_approval = False
						invoice.rejected_by_employee_id = supervisor_id
						invoice.rejected_at = now
						invoice.rejection_reason = reason
						invoice.approved_by_employee_id = None
						invoice.approved_at = None
				else:
					if invoice.status not in {"pending", "approved"}:
						return False, "Solo se puede cancelar una venta activa."
					invoice.manager_approval = False
					invoice.cancelled_by_employee_id = supervisor_id
					invoice.cancelled_at = now
					invoice.cancellation_reason = reason
					invoice.approved_by_employee_id = None
					invoice.approved_at = None
					invoice.rejected_by_employee_id = None
					invoice.rejected_at = None
					invoice.rejection_reason = None

				invoice.status = decision
				session.commit()
			return True, f"Factura {invoice_id}: {decision}."
		except Exception as error:
			return False, f"No se pudo revisar la factura: {error}"

	@classmethod
	def _validate_addons(cls, addons: dict) -> dict[str, dict | None]:
		specifications = {
			"trade_in": ({"old_vehicle_id"}, {"allowance"}),
			"financing": ({"source"}, set()),
			"insurance": ({"company", "policy_number"}, set()),
			"warranty": ({"type"}, {"extended_cost"}),
			"customization": ({"type"}, {"cost"}),
		}
		normalized: dict[str, dict | None] = {}
		for name, (required, money_fields) in specifications.items():
			values = addons.get(name)
			if values is None:
				normalized[name] = None
				continue
			if not isinstance(values, dict):
				raise ValueError(f"Los datos de {name} deben ser un diccionario.")
			data = dict(values)
			missing_fields = required - data.keys()
			if missing_fields:
				missing = ", ".join(sorted(missing_fields))
				raise ValueError(f"Faltan campos de {name}: {missing}.")
			for field in money_fields:
				if field in data:
					data[field] = cls._to_nonnegative_decimal(
						data[field], f"El importe de {name}"
					)
			if name == "trade_in":
				vin = data["old_vehicle_id"]
				if not isinstance(vin, str) or not cls._VIN_PATTERN.fullmatch(
					vin.strip().upper()
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

	@staticmethod
	def _add_sale_addons(invoice: SalesInvoice, addons: dict) -> None:
		if addons["trade_in"]:
			invoice.trade_ins.append(TradeIn(**addons["trade_in"]))
		if addons["financing"]:
			invoice.financing.append(Financing(**addons["financing"]))
		if addons["customization"]:
			invoice.customizations.append(Customization(**addons["customization"]))
		if addons["insurance"]:
			invoice.insurances.append(Insurance(**addons["insurance"]))
		if addons["warranty"]:
			invoice.warranties.append(Warranty(**addons["warranty"]))

	@classmethod
	def _to_nonnegative_decimal(cls, value, label: str) -> Decimal:
		try:
			amount = Decimal(str(value))
		except (InvalidOperation, TypeError, ValueError) as error:
			raise ValueError(f"{label} debe ser un número válido.") from error
		if not amount.is_finite() or amount < 0:
			raise ValueError(f"{label} debe ser un monto no negativo.")
		return amount.quantize(cls._CENT, rounding=ROUND_HALF_UP)
