import re

from models.customer import Customer


class CustomerController:
	"""Coordina las operaciones de clientes entre la vista y el modelo."""

	_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

	def list_customers(self):
		"""Obtiene todos los clientes desde el modelo."""
		return Customer.get_all()

	def register_customer(
		self,
		first_name,
		last_name,
		email,
		phone,
		address,
		lead_source,
	):
		"""Valida y guarda un cliente, retornando éxito y un mensaje."""
		if not isinstance(first_name, str) or not first_name.strip():
			return False, "El nombre es obligatorio."
		if not isinstance(last_name, str) or not last_name.strip():
			return False, "El apellido es obligatorio."
		if not isinstance(email, str) or not email.strip():
			return False, "El correo electrónico es obligatorio."

		email = email.strip()
		if not self._EMAIL_PATTERN.fullmatch(email):
			return False, "El formato del correo electrónico no es válido."

		customer = Customer(
			first_name=first_name.strip(),
			last_name=last_name.strip(),
			email=email,
			phone=phone,
			address=address,
			lead_source=lead_source,
		)
		try:
			customer.save()
			return True, "Cliente registrado correctamente."
		except Exception as error:
			return False, f"No se pudo registrar el cliente: {error}"

	def delete_customer(self, customer_id):
		"""Elimina un cliente invocando el método del modelo."""
		try:
			Customer.delete(customer_id)
			return True, "Cliente eliminado correctamente."
		except Exception as error:
			return False, f"No se pudo eliminar el cliente: {error}"
