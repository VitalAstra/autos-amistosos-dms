"""Modelos ORM para los complementos existentes de facturas."""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base

if TYPE_CHECKING:
	from models.sales_invoice import SalesInvoice


class TradeIn(Base):
	__tablename__ = "trade_in"

	id: Mapped[int] = mapped_column(
		"trade_in_id", Integer, primary_key=True, autoincrement=True
	)
	sales_invoice_number: Mapped[int] = mapped_column(
		ForeignKey("sales_invoice.sales_invoice_number"), nullable=False, unique=True
	)
	old_vehicle_id: Mapped[str] = mapped_column(
		"trade_in_old_vehicle_id", String(17), nullable=False
	)
	allowance: Mapped[Decimal] = mapped_column(
		"trade_in_allowance", Numeric(12, 2), nullable=False
	)
	sales_invoice: Mapped["SalesInvoice"] = relationship(
		"SalesInvoice", back_populates="trade_in"
	)


class Financing(Base):
	__tablename__ = "financing"

	id: Mapped[int] = mapped_column(
		"financing_id", Integer, primary_key=True, autoincrement=True
	)
	sales_invoice_number: Mapped[int] = mapped_column(
		ForeignKey("sales_invoice.sales_invoice_number"), nullable=False, unique=True
	)
	source: Mapped[str] = mapped_column(
		"financing_source", String(50), nullable=False
	)
	bank_name: Mapped[str | None] = mapped_column("financing_bank_name", String(100))
	sales_invoice: Mapped["SalesInvoice"] = relationship(
		"SalesInvoice", back_populates="financing"
	)


class Insurance(Base):
	__tablename__ = "insurance"

	id: Mapped[int] = mapped_column(
		"insurance_id", Integer, primary_key=True, autoincrement=True
	)
	sales_invoice_number: Mapped[int] = mapped_column(
		ForeignKey("sales_invoice.sales_invoice_number"), nullable=False, unique=True
	)
	company: Mapped[str] = mapped_column(
		"insurance_company", String(100), nullable=False
	)
	policy_number: Mapped[str] = mapped_column(
		"insurance_policy_number", String(50), nullable=False
	)
	proof_submitted: Mapped[bool | None] = mapped_column(
		"insurance_proof_submitted", Boolean, default=False
	)
	sales_invoice: Mapped["SalesInvoice"] = relationship(
		"SalesInvoice", back_populates="insurance"
	)


class Warranty(Base):
	__tablename__ = "warranty"

	id: Mapped[int] = mapped_column(
		"warranty_id", Integer, primary_key=True, autoincrement=True
	)
	sales_invoice_number: Mapped[int] = mapped_column(
		ForeignKey("sales_invoice.sales_invoice_number"), nullable=False, unique=True
	)
	type: Mapped[str] = mapped_column("warranty_type", String(50), nullable=False)
	extended_cost: Mapped[Decimal | None] = mapped_column(
		"warranty_extended_cost", Numeric(10, 2), default=Decimal("0")
	)
	sales_invoice: Mapped["SalesInvoice"] = relationship(
		"SalesInvoice", back_populates="warranty"
	)


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
		"customization_cost", Numeric(10, 2), nullable=False, default=Decimal("0")
	)
	sales_invoice: Mapped["SalesInvoice"] = relationship(
		"SalesInvoice", back_populates="customization"
	)
