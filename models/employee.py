"""Modelo ORM mínimo para referenciar al empleado de una factura."""

from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


class Employee(Base):
	__tablename__ = "employee"

	employee_id: Mapped[int] = mapped_column(
		Integer, primary_key=True, autoincrement=True
	)
