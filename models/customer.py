from models.base_model import BaseModel


class Customer(BaseModel):
	"""Modelo de acceso a la tabla customer."""

	def __init__(
		self,
		customer_id=None,
		first_name=None,
		last_name=None,
		email=None,
		phone=None,
		address=None,
		lead_source=None,
	):
		self.customer_id = customer_id
		self.first_name = first_name
		self.last_name = last_name
		self.email = email
		self.phone = phone
		self.address = address
		self.lead_source = lead_source

	@classmethod
	def get_all(cls):
		"""Retorna todos los clientes como una lista de diccionarios."""
		query = """
			SELECT customer_id, first_name, last_name, email, phone, address, lead_source
			FROM customer
		"""
		return cls.execute_query(query, fetchall=True)

	@classmethod
	def get_by_id(cls, customer_id):
		"""Busca un cliente por su clave primaria."""
		query = """
			SELECT customer_id, first_name, last_name, email, phone, address, lead_source
			FROM customer
			WHERE customer_id = %s
		"""
		return cls.execute_query(query, (customer_id,), fetchone=True)

	def save(self):
		"""Inserta el cliente o actualiza el registro existente."""
		if self.customer_id is None:
			query = """
				INSERT INTO customer (first_name, last_name, email, phone, address, lead_source)
				VALUES (%s, %s, %s, %s, %s, %s)
				RETURNING customer_id
			"""
			result = self.execute_query(
				query,
				(
					self.first_name,
					self.last_name,
					self.email,
					self.phone,
					self.address,
					self.lead_source,
				),
				fetchone=True,
			)
			self.customer_id = result["customer_id"]
		else:
			query = """
				UPDATE customer
				SET first_name = %s,
					last_name = %s,
					email = %s,
					phone = %s,
					address = %s,
					lead_source = %s
				WHERE customer_id = %s
			"""
			self.execute_query(
				query,
				(
					self.first_name,
					self.last_name,
					self.email,
					self.phone,
					self.address,
					self.lead_source,
					self.customer_id,
				),
			)
		return self

	@classmethod
	def delete(cls, customer_id):
		"""Elimina un cliente por su clave primaria."""
		query = "DELETE FROM customer WHERE customer_id = %s"
		return cls.execute_query(query, (customer_id,))
