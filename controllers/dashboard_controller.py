"""Consultas agregadas para el panel principal."""

from datetime import date

from sqlalchemy import func, select

from config.database import SessionLocal
from models.customer import Customer
from models.sales_invoice import SalesInvoice
from models.vehicle import Vehicle


class DashboardController:
	_ACTIVE_SALE_STATUSES = ("approved", "completed")

	def get_dashboard_data(self) -> dict:
		month_start = date.today().replace(day=1)
		available_vehicle = ~Vehicle.sales_invoices.any(
			SalesInvoice.status.in_(("pending", *self._ACTIVE_SALE_STATUSES))
		)
		with SessionLocal() as session:
			available_count = session.scalar(
				select(func.count()).select_from(Vehicle).where(available_vehicle)
			)
			monthly_sales = session.scalar(
				select(func.count())
				.select_from(SalesInvoice)
				.where(
					SalesInvoice.status.in_(self._ACTIVE_SALE_STATUSES),
					SalesInvoice.date >= month_start,
				)
			)
			prospects = session.scalar(
				select(func.count())
				.select_from(Customer)
				.where(Customer.status_type == "Potential")
			)
			revenue = session.scalar(
				select(func.coalesce(func.sum(SalesInvoice.total_amount), 0)).where(
					SalesInvoice.status.in_(self._ACTIVE_SALE_STATUSES)
				)
			)
			recent_sales = session.execute(
				select(
					SalesInvoice.id.label("invoice_number"),
					func.concat_ws(" ", Customer.first_name, Customer.last_name).label(
						"customer_name"
					),
					func.concat(Vehicle.manufacturer, " ", Vehicle.model).label("vehicle"),
					SalesInvoice.total_amount.label("amount"),
					SalesInvoice.date.label("date"),
				)
				.join(Customer, SalesInvoice.customer_id == Customer.id)
				.join(Vehicle, SalesInvoice.vehicle_id == Vehicle.id)
				.where(SalesInvoice.status.in_(self._ACTIVE_SALE_STATUSES))
				.order_by(SalesInvoice.date.desc(), SalesInvoice.id.desc())
				.limit(5)
			).mappings().all()

		return {
			"vehicles_available": int(available_count or 0),
			"monthly_sales": int(monthly_sales or 0),
			"new_prospects": int(prospects or 0),
			"invoiced_revenue": f"${revenue:,.2f}",
			"recent_sales": recent_sales,
		}