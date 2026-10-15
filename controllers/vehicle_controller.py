"""Operaciones de inventario mediante SQLAlchemy ORM."""

from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy import select

from config.database import SessionLocal
from models.sales_invoice import SalesInvoice
from models.vehicle import Vehicle


class VehicleController:
	"""Consulta y registra vehículos usando sesiones ORM."""

	_VEHICLE_FIELDS = frozenset(
		{
			"condition",
			"manufacturer",
			"model",
			"manufacture_date",
			"manufacture_location",
			"cylinder_count",
			"door_count",
			"weight",
			"capacity",
			"color",
			"factory_options",
			"list_price",
			"delivery_date",
			"delivery_mileage",
		}
	)
	_INTEGER_FIELDS = frozenset(
		{"cylinder_count", "door_count", "capacity", "delivery_mileage"}
	)
	_DATE_FIELDS = frozenset({"manufacture_date", "delivery_date"})
	_LENGTH_LIMITS = {
		"condition": 10,
		"manufacturer": 50,
		"model": 50,
		"manufacture_location": 100,
		"color": 30,
	}

	def get_inventory(self, available_only: bool = True) -> list[Vehicle]:
		"""Retorna el inventario, filtrando disponibles de forma predeterminada."""
		statement = select(Vehicle)
		if available_only:
			statement = statement.where(
				~Vehicle.sales_invoices.any(
					SalesInvoice.status.in_(("pending", "approved", "completed"))
				)
			)
		with SessionLocal() as session:
			return session.scalars(statement).all()

	def add_vehicle(self, vehicle_data: dict) -> tuple[bool, str]:
		"""Valida y persiste un vehículo nuevo."""
		if not isinstance(vehicle_data, dict):
			return False, "Los datos del vehículo deben ser un diccionario."

		vehicle_id = vehicle_data.get("id", vehicle_data.get("vehicle_id"))
		if not isinstance(vehicle_id, str) or len(vehicle_id.strip()) != 17:
			return False, "El VIN debe tener exactamente 17 caracteres."
		for field in ("manufacturer", "model"):
			value = vehicle_data.get(field)
			if not isinstance(value, str) or not value.strip():
				return False, f"{field.capitalize()} es obligatorio."
			if len(value.strip()) > 50:
				return False, f"{field.capitalize()} no puede superar 50 caracteres."

		normalized_data = {
			key: value.strip() if isinstance(value, str) else value
			for key, value in vehicle_data.items()
			if key in self._VEHICLE_FIELDS
		}
		normalized_data["id"] = vehicle_id.strip().upper()
		for field, maximum in self._LENGTH_LIMITS.items():
			value = normalized_data.get(field)
			if value and len(value) > maximum:
				return False, f"{field} no puede exceder {maximum} caracteres."
		for field in self._INTEGER_FIELDS:
			value = normalized_data.get(field)
			if value in (None, ""):
				normalized_data[field] = None
				continue
			try:
				normalized_data[field] = int(value)
			except (TypeError, ValueError):
				return False, f"{field} debe ser un número entero."
			if normalized_data[field] < 0:
				return False, f"{field} no puede ser negativo."
		for field in self._DATE_FIELDS:
			value = normalized_data.get(field)
			if value in (None, ""):
				normalized_data[field] = None
				continue
			try:
				normalized_data[field] = date.fromisoformat(value)
			except (TypeError, ValueError):
				return False, f"{field} debe tener formato AAAA-MM-DD."
		for field in ("weight", "list_price"):
			value = normalized_data.get(field)
			if field == "weight" and value in (None, ""):
				normalized_data[field] = None
				continue
			try:
				amount = Decimal(str(value))
			except (InvalidOperation, TypeError, ValueError):
				return False, f"{field} debe ser un monto válido."
			if not amount.is_finite() or amount < 0:
				return False, f"{field} debe ser un monto no negativo."
			normalized_data[field] = amount
		if normalized_data["list_price"] <= 0:
			return False, "El precio de lista debe ser mayor a 0."
		for required_field in ("manufacturer", "model"):
			if not normalized_data.get(required_field):
				return False, f"{required_field} es obligatorio."

		try:
			with SessionLocal() as session:
				session.add(Vehicle(**normalized_data))
				session.commit()
			return True, "Vehículo registrado correctamente."
		except Exception as error:
			return False, f"No se pudo registrar el vehículo: {error}"

	def register_vehicle(self, data_dict: dict) -> tuple[bool, str]:
		"""Mantiene compatibilidad con el nombre anterior del método."""
		return self.add_vehicle(data_dict)

	def delete_vehicle(self, vehicle_id: str) -> tuple[bool, str]:
		"""Elimina un vehículo si no está referenciado por ninguna venta."""
		if not isinstance(vehicle_id, str) or len(vehicle_id.strip()) != 17:
			return False, "El VIN seleccionado no es válido."

		normalized_id = vehicle_id.strip().upper()
		try:
			with SessionLocal() as session:
				vehicle = session.scalars(
					select(Vehicle)
					.where(Vehicle.id == normalized_id)
					.with_for_update()
				).one_or_none()
				if vehicle is None:
					return False, "No se encontró el vehículo seleccionado."

				has_sales = session.scalar(
					select(SalesInvoice.id)
					.where(SalesInvoice.vehicle_id == normalized_id)
					.limit(1)
				)
				if has_sales is not None:
					return (
						False,
						"No se puede eliminar este vehículo porque tiene "
						"ventas asociadas.",
					)

				session.delete(vehicle)
				session.commit()
			return True, "Vehículo eliminado correctamente."
		except Exception as error:
			return False, f"No se pudo eliminar el vehículo: {error}"
