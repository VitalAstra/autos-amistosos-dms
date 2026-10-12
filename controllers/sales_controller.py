"""Operaciones transaccionales y ciclo de aprobación de ventas."""

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

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
	"""Registra ventas y comprueba la disponibilidad mediante facturas."""

	_CENT = Decimal("0.01")

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
			subtotal, tax_amount, total_amount = calculate_sale_totals(
				price, license_fee, addons
			)
			customer_id = int(sale_data["customer_id"])
			employee_id = int(sale_data["employee_id"])
			current_mileage = int(sale_data["sales_current_mileage"])
			vehicle_id = str(sale_data["vehicle_id"]).strip().upper()
			if current_mileage < 0:
				raise ValueError("El kilometraje no puede ser negativo.")
			if len(vehicle_id) != 17:
				raise ValueError("El VIN debe tener exactamente 17 caracteres.")

			with SessionLocal() as session:
				try:
					vehicle = session.scalars(
						select(Vehicle)
						.where(Vehicle.id == vehicle_id)
						.with_for_update()
					).one_or_none()
					if vehicle is None:
						raise ValueError("No se encontró el vehículo seleccionado.")
					if self._vehicle_is_unavailable(session, vehicle.id):
						raise ValueError("El vehículo seleccionado ya no está disponible.")
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
					self._add_sale_addons(session, invoice, addons)
					session.commit()
					invoice_id = invoice.id
				except Exception:
					session.rollback()
					raise

			return True, f"Venta {invoice_id} enviada a aprobación del supervisor."
		except Exception as error:
			return False, str(error)

	def list_reviewable_sales(self):
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

	def list_pending_sales(self):
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
			return False, str(error)

	@staticmethod
	def _vehicle_is_unavailable(session, vehicle_id):
		return (
			session.scalar(
				select(SalesInvoice.id)
				.where(
					SalesInvoice.vehicle_id == vehicle_id,
					SalesInvoice.status.in_(("pending", "approved", "completed")),
				)
				.limit(1)
			)
			is not None
		)

	@staticmethod
	def _add_sale_addons(session, invoice, addons):
		trade_in = addons.get("trade_in")
		if trade_in:
			old_vehicle_id = str(trade_in.get("old_vehicle_id", "")).strip().upper()
			if len(old_vehicle_id) != 17:
				raise ValueError("El VIN del vehículo recibido debe tener 17 caracteres.")
			invoice.trade_ins.append(
				TradeIn(
					old_vehicle_id=old_vehicle_id,
					allowance=SalesController._to_nonnegative_decimal(
						trade_in.get("allowance"), "El valor del trade-in"
					),
				)
			)

		financing = addons.get("financing")
		if financing:
			source = str(financing.get("source", "")).strip()
			if not source:
				raise ValueError("La fuente de financiamiento es obligatoria.")
			invoice.financing.append(
				Financing(source=source, bank_name=financing.get("bank_name"))
			)

		customization = addons.get("customization")
		if customization:
			customization_type = str(customization.get("type", "")).strip()
			if not customization_type:
				raise ValueError("El tipo de personalización es obligatorio.")
			invoice.customizations.append(
				Customization(
					type=customization_type,
					cost=SalesController._to_nonnegative_decimal(
						customization.get("cost"), "El costo de personalización"
					),
				)
			)

		insurance = addons.get("insurance")
		if insurance:
			company = str(insurance.get("company", "")).strip()
			policy_number = str(insurance.get("policy_number", "")).strip()
			if not company or not policy_number:
				raise ValueError("Aseguradora y número de póliza son obligatorios.")
			invoice.insurances.append(
				Insurance(
					company=company,
					policy_number=policy_number,
					proof_submitted=bool(insurance.get("proof_submitted")),
				)
			)

		warranty = addons.get("warranty")
		if warranty:
			warranty_type = str(warranty.get("type", "")).strip()
			if not warranty_type:
				raise ValueError("El tipo de garantía es obligatorio.")
			invoice.warranties.append(
				Warranty(
					type=warranty_type,
					extended_cost=SalesController._to_nonnegative_decimal(
						warranty.get("extended_cost", 0), "El costo de garantía"
					),
				)
			)

	@classmethod
	def _to_nonnegative_decimal(cls, value, label: str) -> Decimal:
		try:
			amount = Decimal(str(value))
		except (InvalidOperation, TypeError, ValueError) as error:
			raise ValueError(f"{label} debe ser un número válido.") from error
		if not amount.is_finite() or amount < 0:
			raise ValueError(f"{label} debe ser un monto no negativo.")
		return amount.quantize(cls._CENT, rounding=ROUND_HALF_UP)
