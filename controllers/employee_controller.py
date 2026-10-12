"""Consultas de empleados para selección en ventas y aprobación."""

from sqlalchemy import select

from config.database import SessionLocal
from models.employee import Employee


class EmployeeController:
	def list_active_salespeople(self) -> list[Employee]:
		with SessionLocal() as session:
			return session.scalars(
				select(Employee)
				.where(Employee.role.ilike("salesperson"), Employee.is_active.is_(True))
				.order_by(Employee.last_name, Employee.first_name)
			).all()

	def list_active_supervisors(self) -> list[Employee]:
		with SessionLocal() as session:
			return session.scalars(
				select(Employee)
				.where(
					Employee.role.ilike("manager") | Employee.role.ilike("administrator"),
					Employee.is_active.is_(True),
				)
				.order_by(Employee.last_name, Employee.first_name)
			).all()