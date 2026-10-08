"""Modelo ORM de facturas sobre las columnas existentes de PostgreSQL."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base

if TYPE_CHECKING:
	from models.customer import Customer
	from models.vehicle import Vehicle


class SalesInvoice(Base):
	__tablename__ = "sales_invoice"

	id: Mapped[int] = mapped_column(
		"sales_invoice_number", Integer, primary_key=True, autoincrement=True
	)
	date: Mapped[date] = mapped_column("sales_date", Date, nullable=False, default=date.today)
	customer_id: Mapped[int] = mapped_column(
		"customer_id", ForeignKey("customer.customer_id"), nullable=False
	)
	employee_id: Mapped[int] = mapped_column(
		"employee_id", ForeignKey("employee.employee_id"), nullable=False
	)
	vehicle_id: Mapped[str] = mapped_column(
		"vehicle_id", ForeignKey("vehicle.vehicle_id"), nullable=False
	)
	current_mileage: Mapped[int | None] = mapped_column(
		"sales_current_mileage", Integer
	)
	negotiated_price: Mapped[Decimal] = mapped_column(
		"sales_negotiated_price", Numeric(12, 2), nullable=False
	)
	manager_approval: Mapped[bool | None] = mapped_column(
		"sales_manager_approval", Boolean
	)
	tax_amount: Mapped[Decimal] = mapped_column(
		"sales_tax_amount", Numeric(12, 2), nullable=False
	)
	license_fee_amount: Mapped[Decimal] = mapped_column(
		"sales_license_fee_amount", Numeric(12, 2), nullable=False, default=Decimal("0")
	)
	total_amount: Mapped[Decimal] = mapped_column(
		"sales_total_amount", Numeric(12, 2), nullable=False
	)

	customer: Mapped["Customer"] = relationship("Customer", back_populates="sales_invoices")
	vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="sales_invoices")
