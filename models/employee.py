"""Modelo ORM de empleados para asignar las facturas de venta."""

from decimal import Decimal

from sqlalchemy import Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


class Employee(Base):
	__tablename__ = "employee"

	employee_id: Mapped[int] = mapped_column(
		Integer, primary_key=True, autoincrement=True
	)
	first_name: Mapped[str] = mapped_column(
		"employee_first_name", String(50), nullable=False
	)
	last_name: Mapped[str] = mapped_column(
		"employee_last_name", String(50), nullable=False
	)
	role: Mapped[str] = mapped_column("employee_role", String(30), nullable=False)
	commission_rate: Mapped[Decimal | None] = mapped_column(
		"employee_commission_rate", Numeric(5, 2)
	)
