"""Modelo ORM de empleados, vendedores y supervisores."""

from decimal import Decimal

from sqlalchemy import Boolean, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


class Employee(Base):
	__tablename__ = "employee"
	__table_args__ = (Index("uq_employee_username", "employee_username", unique=True),)

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
	username: Mapped[str | None] = mapped_column("employee_username", String(50))
	password_hash: Mapped[str | None] = mapped_column(
		"employee_password_hash", String(255)
	)
	is_active: Mapped[bool] = mapped_column(
		"employee_is_active",
		Boolean,
		nullable=False,
		default=True,
		server_default="true",
	)
