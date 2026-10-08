from models.base_model import BaseModel


class SalesInvoice(BaseModel):
	"""Modelo de acceso a la tabla sales_invoice."""

	def __init__(
		self,
		sales_invoice_number=None,
		sales_date=None,
		customer_id=None,
		employee_id=None,
		vehicle_id=None,
		sales_current_mileage=None,
		sales_negotiated_price=None,
		sales_manager_approval=None,
		sales_tax_amount=None,
		sales_license_fee_amount=None,
		sales_total_amount=None,
	):
		self.sales_invoice_number = sales_invoice_number
		self.sales_date = sales_date
		self.customer_id = customer_id
		self.employee_id = employee_id
		self.vehicle_id = vehicle_id
		self.sales_current_mileage = sales_current_mileage
		self.sales_negotiated_price = sales_negotiated_price
		self.sales_manager_approval = sales_manager_approval
		self.sales_tax_amount = sales_tax_amount
		self.sales_license_fee_amount = sales_license_fee_amount
		self.sales_total_amount = sales_total_amount

	@classmethod
	def get_sales_summary(cls):
		"""Retorna número, fecha, cliente, vehículo y total de cada venta."""
		query = """
			SELECT
				si.sales_invoice_number AS "Número Factura",
				si.sales_date AS "Fecha",
				CONCAT_WS(' ', c.first_name, c.last_name) AS "Nombre Cliente",
				v.model AS "Modelo Vehículo",
				si.sales_total_amount AS "Monto Total"
			FROM sales_invoice AS si
			JOIN customer AS c ON c.customer_id = si.customer_id
			JOIN vehicle AS v ON v.vehicle_id = si.vehicle_id
		"""
		return cls.execute_query(query, fetchall=True)
