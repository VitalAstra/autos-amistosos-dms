"""Modelo ORM de vehículos con columnas existentes de PostgreSQL."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base

if TYPE_CHECKING:
	from models.sales_invoice import SalesInvoice


class Vehicle(Base):
	__tablename__ = "vehicle"

	id: Mapped[str] = mapped_column("vehicle_id", String(17), primary_key=True)
	condition: Mapped[str | None] = mapped_column("vehicle_condition", String(10))
	manufacturer: Mapped[str | None] = mapped_column(
		"vehicle_manufacturer", String(50), nullable=False
	)
	model: Mapped[str] = mapped_column("vehicle_model", String(50), nullable=False)
	manufacture_date: Mapped[date | None] = mapped_column(
		"vehicle_manufacture_date", Date
	)
	manufacture_location: Mapped[str | None] = mapped_column(
		"vehicle_manufacture_location", String(100)
	)
	cylinder_count: Mapped[int | None] = mapped_column(
		"vehicle_cylinder_count", Integer
	)
	door_count: Mapped[int | None] = mapped_column("vehicle_door_count", Integer)
	weight: Mapped[Decimal | None] = mapped_column(
		"vehicle_weight", Numeric(8, 2)
	)
	capacity: Mapped[int | None] = mapped_column("vehicle_capacity", Integer)
	color: Mapped[str | None] = mapped_column("vehicle_color", String(30))
	factory_options: Mapped[str | None] = mapped_column(
		"vehicle_factory_options", Text
	)
	list_price: Mapped[Decimal] = mapped_column(
		"vehicle_list_price", Numeric(12, 2), nullable=False
	)
	delivery_date: Mapped[date | None] = mapped_column(
		"vehicle_delivery_date", Date
	)
	delivery_mileage: Mapped[int | None] = mapped_column(
		"vehicle_delivery_mileage", Integer
	)

	sales_invoices: Mapped[list["SalesInvoice"]] = relationship(
		back_populates="vehicle"
	)
