"""Operaciones de clientes mediante SQLAlchemy ORM."""

import re

from sqlalchemy import select

from config.database import SessionLocal
from models.customer import Customer


class CustomerController:
	"""Coordina las operaciones de clientes."""

	_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
	_FIELD_ALIASES = {
		"customer_first_name": "first_name",
		"customer_last_name": "last_name",
		"customer_email": "email",
		"customer_phone": "phone",
		"customer_address": "address",
		"customer_status_type": "status_type",
		"customer_lead_source": "lead_source",
	}
	_CUSTOMER_FIELDS = frozenset(
		{
			"first_name",
			"last_name",
			"email",
			"phone",
			"address",
			"status_type",
			"lead_source",
		}
	)

	def list_customers(self) -> list[Customer]:
		"""Retorna todos los clientes usando una consulta ORM."""
		with SessionLocal() as session:
			return session.scalars(select(Customer)).all()

	def register_customer(self, data: dict) -> tuple[bool, str]:
		"""Valida y persiste un nuevo cliente."""
		if not isinstance(data, dict):
			return False, "Los datos del cliente deben ser un diccionario."

		customer_data = self._normalize_data(data)
		first_name = customer_data.get("first_name")
		last_name = customer_data.get("last_name")
		email = customer_data.get("email")
		if not isinstance(first_name, str) or not first_name.strip():
			return False, "El nombre es obligatorio."
		if not isinstance(last_name, str) or not last_name.strip():
			return False, "El apellido es obligatorio."
		if not isinstance(email, str) or not email.strip():
			return False, "El correo electrónico es obligatorio."

		email = email.strip()
		if not self._EMAIL_PATTERN.fullmatch(email):
			return False, "El formato del correo electrónico no es válido."

		customer_data.update(
			first_name=first_name.strip(),
			last_name=last_name.strip(),
			email=email,
		)
		try:
			with SessionLocal() as session:
				session.add(Customer(**customer_data))
				session.commit()
			return True, "Cliente registrado correctamente."
		except Exception as error:
			return False, f"No se pudo registrar el cliente: {error}"

	def get_customer_by_id(self, customer_id: int) -> Customer | None:
		"""Busca un cliente por su clave primaria."""
		with SessionLocal() as session:
			return session.get(Customer, customer_id)

	def update_customer(self, customer_id: int, data: dict) -> tuple[bool, str]:
		"""Actualiza los campos proporcionados de un cliente."""
		if not isinstance(data, dict):
			return False, "Los datos del cliente deben ser un diccionario."

		customer_data = self._normalize_data(data)
		if "email" in customer_data:
			email = customer_data["email"]
			if not isinstance(email, str) or not self._EMAIL_PATTERN.fullmatch(
				email.strip()
			):
				return False, "El formato del correo electrónico no es válido."
			customer_data["email"] = email.strip()

		try:
			with SessionLocal() as session:
				customer = session.get(Customer, customer_id)
				if customer is None:
					return False, "No se encontró el cliente."
				for field, value in customer_data.items():
					setattr(customer, field, value)
				session.commit()
			return True, "Cliente actualizado correctamente."
		except Exception as error:
			return False, f"No se pudo actualizar el cliente: {error}"

	def delete_customer(self, customer_id: int) -> tuple[bool, str]:
		"""Elimina un cliente existente."""
		try:
			with SessionLocal() as session:
				customer = session.get(Customer, customer_id)
				if customer is None:
					return False, "No se encontró el cliente."
				session.delete(customer)
				session.commit()
			return True, "Cliente eliminado correctamente."
		except Exception as error:
			return False, f"No se pudo eliminar el cliente: {error}"

	@classmethod
	def _normalize_data(cls, data: dict) -> dict:
		normalized = {
			cls._FIELD_ALIASES.get(key, key): value for key, value in data.items()
		}
		return {
			key: value
			for key, value in normalized.items()
			if key in cls._CUSTOMER_FIELDS
		}
