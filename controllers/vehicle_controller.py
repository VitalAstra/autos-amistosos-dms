from decimal import Decimal, InvalidOperation

from models.vehicle import Vehicle


class VehicleController:
	"""Gestiona las operaciones del catálogo de vehículos."""

	def get_inventory(self, available_only=False):
		"""Retorna todo el inventario o solo los vehículos disponibles."""
		if available_only:
			return Vehicle.get_available_vehicles()
		return Vehicle.get_all()

	def register_vehicle(self, data_dict):
		"""Valida y registra un vehículo desde sus atributos."""
		if not isinstance(data_dict, dict):
			return False, "Los datos del vehículo deben ser un diccionario."

		vin = data_dict.get("vehicle_id")
		if not isinstance(vin, str) or len(vin.strip()) != 17:
			return False, "El VIN debe tener exactamente 17 caracteres."

		try:
			list_price = Decimal(str(data_dict.get("list_price")))
		except (InvalidOperation, TypeError, ValueError):
			return False, "El precio de lista debe ser un número mayor que 0."

		if not list_price.is_finite() or list_price <= 0:
			return False, "El precio de lista debe ser un número mayor que 0."

		vehicle_data = dict(data_dict)
		vehicle_data["vehicle_id"] = vin.strip()
		vehicle_data["list_price"] = list_price
		try:
			Vehicle(**vehicle_data).save()
			return True, "Vehículo registrado correctamente."
		except Exception as error:
			return False, f"No se pudo registrar el vehículo: {error}"
