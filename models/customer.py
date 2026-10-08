"""Modelo ORM de clientes con atributos Python desacoplados de PostgreSQL."""

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base

if TYPE_CHECKING:
	from models.sales_invoice import SalesInvoice


class Customer(Base):
	__tablename__ = "customer"

	id: Mapped[int] = mapped_column(
		"customer_id", Integer, primary_key=True, autoincrement=True
	)
	first_name: Mapped[str] = mapped_column(
		"customer_first_name", String(100), nullable=False
	)
	last_name: Mapped[str] = mapped_column(
		"customer_last_name", String(100), nullable=False
	)
	email: Mapped[str] = mapped_column(
		"customer_email", String(255), nullable=False
	)
	phone: Mapped[str | None] = mapped_column("customer_phone", String(20))
	address: Mapped[str | None] = mapped_column("customer_address", String(255))
	status_type: Mapped[str] = mapped_column(
		"customer_status_type",
		String(50),
		nullable=False,
		default="Potential",
	)
	lead_source: Mapped[str | None] = mapped_column(
		"customer_lead_source", String(100)
	)

	sales_invoices: Mapped[list["SalesInvoice"]] = relationship(
		back_populates="customer"
	)
