"""Operaciones de venta mediante transacciones SQLAlchemy ORM."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from sqlalchemy import select

from config.database import SessionLocal
from models.customer import Customer
from models.employee import Employee
from models.sales_invoice import SalesInvoice
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
	) -> tuple[bool, str]:
		"""Registra una factura y marca como vendido el vehículo asociado.

		``tax_rate`` se expresa como fracción: por ejemplo, ``Decimal("0.13")``
		representa un impuesto del 13 por ciento. El empleado es obligatorio
		para guardar la referencia exigida por la factura.
		"""
		try:
			price = self._to_nonnegative_decimal(negotiated_price, "El precio")
			rate = self._to_nonnegative_decimal(tax_rate, "La tasa de impuestos")
			tax_amount = (price * rate).quantize(
				self._CENT, rounding=ROUND_HALF_UP
			)
			total_amount = price + tax_amount

			with SessionLocal() as session:
				try:
					vehicle = session.scalars(
						select(Vehicle)
						.where(Vehicle.id == vehicle_id)
						.with_for_update()
					).one_or_none()
					if vehicle is None:
						raise ValueError("No se encontró el vehículo seleccionado.")
					if vehicle.status != "Available":
						raise ValueError("El vehículo seleccionado ya no está disponible.")
					if session.get(Customer, customer_id) is None:
						raise ValueError("No se encontró el cliente seleccionado.")
					if session.get(Employee, employee_id) is None:
						raise ValueError("No se encontró el empleado seleccionado.")

					invoice = SalesInvoice(
						customer_id=customer_id,
						vehicle_id=vehicle.id,
						employee_id=employee_id,
						negotiated_price=price,
						tax_amount=tax_amount,
						license_fee_amount=Decimal("0.00"),
						total_amount=total_amount,
					)
					vehicle.status = "Sold"
					session.add(invoice)
					session.commit()
					invoice_id = invoice.id
				except Exception:
					session.rollback()
					raise

			return True, f"Venta registrada con factura {invoice_id}."
		except Exception as error:
			return False, str(error)

	@classmethod
	def _to_nonnegative_decimal(cls, value, label: str) -> Decimal:
		try:
			amount = Decimal(str(value))
		except (InvalidOperation, TypeError, ValueError) as error:
			raise ValueError(f"{label} debe ser un número válido.") from error
		if not amount.is_finite() or amount < 0:
			raise ValueError(f"{label} debe ser un monto no negativo.")
		return amount.quantize(cls._CENT, rounding=ROUND_HALF_UP)
