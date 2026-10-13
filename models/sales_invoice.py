"""Modelo ORM de facturas sobre las columnas existentes de PostgreSQL."""

from datetime import date as date_type, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
	Boolean,
	CheckConstraint,
	Date,
	DateTime,
	ForeignKey,
	Index,
	Integer,
	Numeric,
	String,
	text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base

if TYPE_CHECKING:
	from models.customer import Customer
	from models.employee import Employee
	from models.sales_addons import (
		Customization,
		Financing,
		Insurance,
		Survey,
		TradeIn,
		Warranty,
	)
	from models.vehicle import Vehicle


class SalesInvoice(Base):
	__tablename__ = "sales_invoice"
	__table_args__ = (
		CheckConstraint(
			"sales_status IN ('pending', 'approved', 'rejected', 'cancelled', 'completed')",
			name="ck_sales_invoice_sales_status",
		),
		Index(
			"uq_active_sales_invoice_vehicle",
			"vehicle_id",
			unique=True,
			postgresql_where=text(
				"sales_status IN ('pending', 'approved', 'completed')"
			),
		),
	)

	id: Mapped[int] = mapped_column(
		"sales_invoice_number", Integer, primary_key=True, autoincrement=True
	)
	date: Mapped[date_type] = mapped_column(
		"sales_date", Date, nullable=False, default=date_type.today
	)
	customer_id: Mapped[int] = mapped_column(
		"customer_id", ForeignKey("customer.customer_id"), nullable=False
	)
	employee_id: Mapped[int] = mapped_column(
		"employee_id", ForeignKey("employee.employee_id"), nullable=False
	)
	vehicle_id: Mapped[str] = mapped_column(
		"vehicle_id", ForeignKey("vehicle.vehicle_id"), nullable=False
	)
	current_mileage: Mapped[int] = mapped_column(
		"sales_current_mileage", Integer, nullable=False
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
	status: Mapped[str] = mapped_column(
		"sales_status",
		String(20),
		nullable=False,
		default="completed",
		server_default="completed",
	)
	approved_by_employee_id: Mapped[int | None] = mapped_column(
		ForeignKey(
			"employee.employee_id",
			ondelete="SET NULL",
			name="fk_sales_invoice_approved_by",
		)
	)
	approved_at: Mapped[datetime | None] = mapped_column(
		"sales_approved_at", DateTime(timezone=True)
	)
	rejected_by_employee_id: Mapped[int | None] = mapped_column(
		ForeignKey(
			"employee.employee_id",
			ondelete="SET NULL",
			name="fk_sales_invoice_rejected_by",
		)
	)
	rejected_at: Mapped[datetime | None] = mapped_column(
		"sales_rejected_at", DateTime(timezone=True)
	)
	rejection_reason: Mapped[str | None] = mapped_column(
		"sales_rejection_reason", String(250)
	)
	cancelled_by_employee_id: Mapped[int | None] = mapped_column(
		ForeignKey(
			"employee.employee_id",
			ondelete="SET NULL",
			name="fk_sales_invoice_cancelled_by",
		)
	)
	cancelled_at: Mapped[datetime | None] = mapped_column(
		"sales_cancelled_at", DateTime(timezone=True)
	)
	cancellation_reason: Mapped[str | None] = mapped_column(
		"sales_cancellation_reason", String(250)
	)

	customer: Mapped["Customer"] = relationship(back_populates="sales_invoices")
	vehicle: Mapped["Vehicle"] = relationship(back_populates="sales_invoices")
	employee: Mapped["Employee"] = relationship(
		"Employee", foreign_keys=[employee_id]
	)
	financing: Mapped[list["Financing"]] = relationship(back_populates="invoice")
	trade_ins: Mapped[list["TradeIn"]] = relationship(back_populates="invoice")
	customizations: Mapped[list["Customization"]] = relationship(
		back_populates="invoice"
	)
	insurances: Mapped[list["Insurance"]] = relationship(back_populates="invoice")
	warranties: Mapped[list["Warranty"]] = relationship(back_populates="invoice")
	surveys: Mapped[list["Survey"]] = relationship(back_populates="invoice")
