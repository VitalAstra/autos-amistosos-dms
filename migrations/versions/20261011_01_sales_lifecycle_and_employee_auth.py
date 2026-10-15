"""Add invoice lifecycle tracking and employee credentials."""

from alembic import op
import sqlalchemy as sa

revision = "20261011_01"
down_revision = None
branch_labels = None
depends_on = None


def _columns(table_name):
	return {
		column["name"]
		for column in sa.inspect(op.get_bind()).get_columns(table_name)
	}


def _foreign_keys(table_name):
	return {
		foreign_key.get("name")
		for foreign_key in sa.inspect(op.get_bind()).get_foreign_keys(table_name)
	}


def upgrade():
	from config.database import Base
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
	from models.sales_invoice import SalesInvoice
	from models.vehicle import Vehicle

	Base.metadata.create_all(bind=op.get_bind())

	employee_columns = _columns("employee")
	if "employee_username" not in employee_columns:
		op.add_column("employee", sa.Column("employee_username", sa.String(50)))
	if "employee_password_hash" not in employee_columns:
		op.add_column("employee", sa.Column("employee_password_hash", sa.String(255)))
	if "employee_is_active" not in employee_columns:
		op.add_column(
			"employee",
			sa.Column(
				"employee_is_active",
				sa.Boolean(),
				nullable=False,
				server_default=sa.true(),
			),
		)

	employee_indexes = {
		index["name"] for index in sa.inspect(op.get_bind()).get_indexes("employee")
	}
	if "uq_employee_username" not in employee_indexes:
		op.create_index(
			"uq_employee_username", "employee", ["employee_username"], unique=True
		)

	invoice_columns = _columns("sales_invoice")
	if "sales_status" not in invoice_columns:
		op.add_column(
			"sales_invoice",
			sa.Column(
				"sales_status",
				sa.String(20),
				nullable=False,
				server_default="completed",
			),
		)
	for column_name in (
		"sales_approved_by_employee_id",
		"sales_rejected_by_employee_id",
		"sales_cancelled_by_employee_id",
	):
		if column_name not in invoice_columns:
			op.add_column(
				"sales_invoice", sa.Column(column_name, sa.Integer(), nullable=True)
			)
	for column_name in (
		"sales_approved_at",
		"sales_rejected_at",
		"sales_cancelled_at",
	):
		if column_name not in invoice_columns:
			op.add_column(
				"sales_invoice",
				sa.Column(column_name, sa.DateTime(timezone=True), nullable=True),
			)

	for column_name in ("sales_rejection_reason", "sales_cancellation_reason"):
		if column_name not in invoice_columns:
			op.add_column(
				"sales_invoice", sa.Column(column_name, sa.String(250), nullable=True)
			)

	foreign_keys = _foreign_keys("sales_invoice")
	for column_name, constraint_name in (
		("sales_approved_by_employee_id", "fk_sales_invoice_approved_by"),
		("sales_rejected_by_employee_id", "fk_sales_invoice_rejected_by"),
		("sales_cancelled_by_employee_id", "fk_sales_invoice_cancelled_by"),
	):
		if constraint_name not in foreign_keys:
			op.create_foreign_key(
				constraint_name,
				"sales_invoice",
				"employee",
				[column_name],
				["employee_id"],
				ondelete="SET NULL",
			)

	check_constraints = {
		constraint["name"]
		for constraint in sa.inspect(op.get_bind()).get_check_constraints(
			"sales_invoice"
		)
	}
	if "ck_sales_invoice_sales_status" not in check_constraints:
		op.create_check_constraint(
			"ck_sales_invoice_sales_status",
			"sales_invoice",
			sa.column("sales_status").in_(
				("pending", "approved", "rejected", "cancelled", "completed")
			),
		)

	invoice_indexes = {
		index["name"]
		for index in sa.inspect(op.get_bind()).get_indexes("sales_invoice")
	}
	if "uq_active_sales_invoice_vehicle" not in invoice_indexes:
		duplicate_vehicles = (
			sa.select(SalesInvoice.vehicle_id)
			.where(
				SalesInvoice.status.in_(("pending", "approved", "completed"))
			)
			.group_by(SalesInvoice.vehicle_id)
			.having(sa.func.count() > 1)
			.subquery()
		)
		duplicate_count = op.get_bind().execute(
			sa.select(sa.func.count()).select_from(duplicate_vehicles)
		).scalar_one()
		if duplicate_count:
			raise RuntimeError(
				"No se puede garantizar una venta activa por VIN: "
				f"hay {duplicate_count} VIN con facturas activas repetidas. "
				"Los datos se conservaron; revisa esos casos antes de reintentar."
			)
		op.create_index(
			"uq_active_sales_invoice_vehicle",
			"sales_invoice",
			["vehicle_id"],
			unique=True,
			postgresql_where=sa.column("sales_status").in_(
				("pending", "approved", "completed")
			),
		)


def downgrade():
	if "uq_active_sales_invoice_vehicle" in {
		index["name"]
		for index in sa.inspect(op.get_bind()).get_indexes("sales_invoice")
	}:
		op.drop_index("uq_active_sales_invoice_vehicle", table_name="sales_invoice")
	if "ck_sales_invoice_sales_status" in {
		constraint["name"]
		for constraint in sa.inspect(op.get_bind()).get_check_constraints(
			"sales_invoice"
		)
	}:
		op.drop_constraint(
			"ck_sales_invoice_sales_status", "sales_invoice", type_="check"
		)

	for constraint_name in (
		"fk_sales_invoice_approved_by",
		"fk_sales_invoice_rejected_by",
		"fk_sales_invoice_cancelled_by",
	):
		if constraint_name in _foreign_keys("sales_invoice"):
			op.drop_constraint(constraint_name, "sales_invoice", type_="foreignkey")

	for column_name in (
		"sales_status",
		"sales_approved_by_employee_id",
		"sales_rejected_by_employee_id",
		"sales_cancelled_by_employee_id",
		"sales_approved_at",
		"sales_rejected_at",
		"sales_cancelled_at",
		"sales_rejection_reason",
		"sales_cancellation_reason",
	):
		if column_name in _columns("sales_invoice"):
			op.drop_column("sales_invoice", column_name)

	if "uq_employee_username" in {
		index["name"] for index in sa.inspect(op.get_bind()).get_indexes("employee")
	}:
		op.drop_index("uq_employee_username", table_name="employee")
	for column_name in (
		"employee_username",
		"employee_password_hash",
		"employee_is_active",
	):
		if column_name in _columns("employee"):
			op.drop_column("employee", column_name)