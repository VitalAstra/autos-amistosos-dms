"""Modelo ORM de vehículos con columnas existentes de PostgreSQL."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base

if TYPE_CHECKING:
	from models.sales_invoice import SalesInvoice


class Vehicle(Base):
	__tablename__ = "vehicle"

	id: Mapped[str] = mapped_column("vehicle_id", String(17), primary_key=True)
	condition: Mapped[str | None] = mapped_column("vehicle_condition", String(50))
	manufacturer: Mapped[str | None] = mapped_column(
		"vehicle_manufacturer", String(100)
	)
	model: Mapped[str | None] = mapped_column("vehicle_model", String(100))
	manufacture_date: Mapped[date | None] = mapped_column(
		"vehicle_manufacture_date", Date
	)
	list_price: Mapped[Decimal | None] = mapped_column(
		"vehicle_list_price", Numeric(12, 2)
	)
	status: Mapped[str] = mapped_column(
		"vehicle_status", String(30), nullable=False, default="Available"
	)

	sales_invoices: Mapped[list["SalesInvoice"]] = relationship(
		back_populates="vehicle"
	)
