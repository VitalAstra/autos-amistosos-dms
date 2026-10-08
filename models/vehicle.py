from models.base_model import BaseModel


class Vehicle(BaseModel):
	"""Modelo de acceso a la tabla vehicle."""

	def __init__(
		self,
		vehicle_id=None,
		condition=None,
		manufacturer=None,
		model=None,
		manufacture_date=None,
		manufacture_location=None,
		cylinder_count=None,
		door_count=None,
		weight=None,
		capacity=None,
		color=None,
		factory_options=None,
		list_price=None,
		delivery_date=None,
		delivery_mileage=None,
	):
		self.vehicle_id = vehicle_id
		self.condition = condition
		self.manufacturer = manufacturer
		self.model = model
		self.manufacture_date = manufacture_date
		self.manufacture_location = manufacture_location
		self.cylinder_count = cylinder_count
		self.door_count = door_count
		self.weight = weight
		self.capacity = capacity
		self.color = color
		self.factory_options = factory_options
		self.list_price = list_price
		self.delivery_date = delivery_date
		self.delivery_mileage = delivery_mileage

	@classmethod
	def get_all(cls):
		"""Retorna todos los vehículos del inventario."""
		query = """
			SELECT vehicle_id, "condition", manufacturer, model,
				manufacture_date, manufacture_location, cylinder_count,
				door_count, weight, capacity, color, factory_options,
				list_price, delivery_date, delivery_mileage
			FROM vehicle
		"""
		return cls.execute_query(query, fetchall=True)

	@classmethod
	def get_available_vehicles(cls):
		"""Retorna vehículos cuyo VIN no aparece en sales_invoice."""
		query = """
			SELECT v.vehicle_id, v."condition", v.manufacturer, v.model,
				v.manufacture_date, v.manufacture_location, v.cylinder_count,
				v.door_count, v.weight, v.capacity, v.color, v.factory_options,
				v.list_price, v.delivery_date, v.delivery_mileage
			FROM vehicle AS v
			WHERE NOT EXISTS (
				SELECT 1
				FROM sales_invoice AS si
				WHERE si.vehicle_id = v.vehicle_id
			)
		"""
		return cls.execute_query(query, fetchall=True)

	@classmethod
	def get_by_vin(cls, vin):
		"""Busca un vehículo usando su VIN (vehicle_id)."""
		query = """
			SELECT vehicle_id, "condition", manufacturer, model,
				manufacture_date, manufacture_location, cylinder_count,
				door_count, weight, capacity, color, factory_options,
				list_price, delivery_date, delivery_mileage
			FROM vehicle
			WHERE vehicle_id = %s
		"""
		return cls.execute_query(query, (vin,), fetchone=True)

	def save(self):
		"""Inserta el vehículo o actualiza la fila existente para el VIN."""
		query = """
			INSERT INTO vehicle (
				vehicle_id, "condition", manufacturer, model, manufacture_date,
				manufacture_location, cylinder_count, door_count, weight, capacity,
				color, factory_options, list_price, delivery_date, delivery_mileage
			)
			VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
			ON CONFLICT (vehicle_id) DO UPDATE SET
				"condition" = EXCLUDED."condition",
				manufacturer = EXCLUDED.manufacturer,
				model = EXCLUDED.model,
				manufacture_date = EXCLUDED.manufacture_date,
				manufacture_location = EXCLUDED.manufacture_location,
				cylinder_count = EXCLUDED.cylinder_count,
				door_count = EXCLUDED.door_count,
				weight = EXCLUDED.weight,
				capacity = EXCLUDED.capacity,
				color = EXCLUDED.color,
				factory_options = EXCLUDED.factory_options,
				list_price = EXCLUDED.list_price,
				delivery_date = EXCLUDED.delivery_date,
				delivery_mileage = EXCLUDED.delivery_mileage
		"""
		self.execute_query(
			query,
			(
				self.vehicle_id,
				self.condition,
				self.manufacturer,
				self.model,
				self.manufacture_date,
				self.manufacture_location,
				self.cylinder_count,
				self.door_count,
				self.weight,
				self.capacity,
				self.color,
				self.factory_options,
				self.list_price,
				self.delivery_date,
				self.delivery_mileage,
			),
		)
		return self
