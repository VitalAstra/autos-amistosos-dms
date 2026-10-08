"""Operaciones de inventario mediante SQLAlchemy ORM."""

from decimal import Decimal, InvalidOperation

from sqlalchemy import select

from config.database import SessionLocal
from models.vehicle import Vehicle


class VehicleController:
	"""Consulta y registra vehículos usando sesiones ORM."""

	_VEHICLE_FIELDS = frozenset(
		{
			"condition",
			"manufacturer",
			"model",
			"manufacture_date",
			"list_price",
			"status",
		}
	)

	def get_inventory(self, available_only: bool = True) -> list[Vehicle]:
		"""Retorna el inventario, filtrando disponibles de forma predeterminada."""
		statement = select(Vehicle)
		if available_only:
			statement = statement.where(Vehicle.status == "Available")
		with SessionLocal() as session:
			return session.scalars(statement).all()

	def add_vehicle(self, vehicle_data: dict) -> tuple[bool, str]:
		"""Valida y persiste un vehículo nuevo."""
		if not isinstance(vehicle_data, dict):
			return False, "Los datos del vehículo deben ser un diccionario."

		vehicle_id = vehicle_data.get("id", vehicle_data.get("vehicle_id"))
		if not isinstance(vehicle_id, str) or len(vehicle_id.strip()) != 17:
			return False, "El VIN debe tener exactamente 17 caracteres."

		raw_price = vehicle_data.get("list_price")
		try:
			list_price = Decimal(str(raw_price))
		except (InvalidOperation, TypeError, ValueError):
			return False, "El precio de lista debe ser un número mayor que 0."
		if not list_price.is_finite() or list_price <= 0:
			return False, "El precio de lista debe ser un número mayor que 0."

		normalized_data = {
			key: value
			for key, value in vehicle_data.items()
			if key in self._VEHICLE_FIELDS
		}
		normalized_data["id"] = vehicle_id.strip().upper()
		normalized_data["list_price"] = list_price

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
