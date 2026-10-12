"""Modelos ORM de complementos y encuestas de una factura."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base

if TYPE_CHECKING:
	from models.sales_invoice import SalesInvoice


class Financing(Base):
	__tablename__ = "financing"

	id: Mapped[int] = mapped_column(
		"financing_id", Integer, primary_key=True, autoincrement=True
	)
	sales_invoice_number: Mapped[int] = mapped_column(
		ForeignKey("sales_invoice.sales_invoice_number"), nullable=False
	)
	source: Mapped[str] = mapped_column("financing_source", String(50), nullable=False)
	bank_name: Mapped[str | None] = mapped_column("financing_bank_name", String(100))

	invoice: Mapped["SalesInvoice"] = relationship(back_populates="financing")


class TradeIn(Base):
	__tablename__ = "trade_in"

	id: Mapped[int] = mapped_column(
		"trade_in_id", Integer, primary_key=True, autoincrement=True
	)
	sales_invoice_number: Mapped[int] = mapped_column(
		ForeignKey("sales_invoice.sales_invoice_number"), nullable=False
	)
	old_vehicle_id: Mapped[str] = mapped_column(
		"trade_in_old_vehicle_id", String(17), nullable=False
	)
	allowance: Mapped[Decimal] = mapped_column(
		"trade_in_allowance", Numeric(12, 2), nullable=False
	)

	invoice: Mapped["SalesInvoice"] = relationship(back_populates="trade_ins")


class Customization(Base):
	__tablename__ = "customization"

	id: Mapped[int] = mapped_column(
		"customization_id", Integer, primary_key=True, autoincrement=True
	)
	sales_invoice_number: Mapped[int] = mapped_column(
		ForeignKey("sales_invoice.sales_invoice_number"), nullable=False
	)
	type: Mapped[str] = mapped_column(
		"customization_type", String(100), nullable=False
	)
	cost: Mapped[Decimal] = mapped_column(
		"customization_cost", Numeric(10, 2), nullable=False
	)

	invoice: Mapped["SalesInvoice"] = relationship(back_populates="customizations")


class Insurance(Base):
	__tablename__ = "insurance"

	id: Mapped[int] = mapped_column(
		"insurance_id", Integer, primary_key=True, autoincrement=True
	)
	sales_invoice_number: Mapped[int] = mapped_column(
		ForeignKey("sales_invoice.sales_invoice_number"), nullable=False
	)
	company: Mapped[str] = mapped_column(
		"insurance_company", String(100), nullable=False
	)
	policy_number: Mapped[str] = mapped_column(
		"insurance_policy_number", String(50), nullable=False
	)
	proof_submitted: Mapped[bool | None] = mapped_column(
		"insurance_proof_submitted", Boolean
	)

	invoice: Mapped["SalesInvoice"] = relationship(back_populates="insurances")


class Warranty(Base):
	__tablename__ = "warranty"

	id: Mapped[int] = mapped_column(
		"warranty_id", Integer, primary_key=True, autoincrement=True
	)
	sales_invoice_number: Mapped[int] = mapped_column(
		ForeignKey("sales_invoice.sales_invoice_number"), nullable=False
	)
	type: Mapped[str] = mapped_column("warranty_type", String(50), nullable=False)
	extended_cost: Mapped[Decimal | None] = mapped_column(
		"warranty_extended_cost", Numeric(10, 2)
	)

	invoice: Mapped["SalesInvoice"] = relationship(back_populates="warranties")


class Survey(Base):
	__tablename__ = "survey"

	id: Mapped[int] = mapped_column(
		"survey_id", Integer, primary_key=True, autoincrement=True
	)
	sales_invoice_number: Mapped[int] = mapped_column(
		ForeignKey("sales_invoice.sales_invoice_number"), nullable=False
	)
	survey_date: Mapped[date | None] = mapped_column(Date)
	car_rating: Mapped[int | None] = mapped_column("survey_car_rating", Integer)
	dealership_rating: Mapped[int | None] = mapped_column(
		"survey_dealership_rating", Integer
	)
	salesperson_rating: Mapped[int | None] = mapped_column(
		"survey_salesperson_rating", Integer
	)

	invoice: Mapped["SalesInvoice"] = relationship(back_populates="surveys")
