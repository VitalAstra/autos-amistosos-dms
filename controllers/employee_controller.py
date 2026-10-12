"""Consultas ORM de empleados utilizadas por el asistente de ventas."""

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from config.database import SessionLocal
from models.employee import Employee


class EmployeeController:
	"""Proporciona los empleados disponibles para asignar una factura."""

	def list_employees(self) -> list[Employee]:
		with SessionLocal() as session:
			return session.scalars(
				select(Employee).order_by(Employee.last_name, Employee.first_name)
			).all()

	def add_employee(self, employee_data: dict) -> tuple[bool, str]:
		"""Valida y guarda un empleado usando el modelo ORM."""
		if not isinstance(employee_data, dict):
			return False, "Los datos del empleado deben ser un diccionario."

		first_name = employee_data.get("first_name")
		last_name = employee_data.get("last_name")
		role = employee_data.get("role")
		if not isinstance(first_name, str) or not first_name.strip():
			return False, "El nombre es obligatorio."
		if not isinstance(last_name, str) or not last_name.strip():
			return False, "El apellido es obligatorio."
		if not isinstance(role, str) or not role.strip():
			return False, "El puesto es obligatorio."

		try:
			with SessionLocal() as session:
				session.add(
					Employee(
						first_name=first_name.strip(),
						last_name=last_name.strip(),
						role=role.strip(),
					)
				)
				session.commit()
			return True, "Empleado registrado correctamente."
		except SQLAlchemyError as error:
			return False, f"No se pudo registrar el empleado: {error}"
