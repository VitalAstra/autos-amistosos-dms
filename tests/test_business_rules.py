import unittest
from decimal import Decimal
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable
from sqlalchemy.sql.elements import TextClause
from sqlalchemy.orm import sessionmaker

from controllers.auth_controller import AuthController
from controllers.sales_controller import SalesController
from controllers.survey_controller import SurveyController
from controllers.vehicle_controller import VehicleController
from config.database import Base, init_db
from models.customer import Customer
from models.employee import Employee
from models.sales_invoice import SalesInvoice
from models.vehicle import Vehicle
from utils.sales_calculator import calculate_sale_totals


class FakeSession:
	added = None

	def __enter__(self):
		return self

	def __exit__(self, *_):
		return False

	def add(self, instance):
		type(self).added = instance

	def commit(self):
		pass


class BusinessRulesTests(unittest.TestCase):
	def test_survey_prototype_includes_common_inbound_channels(self):
		messages = SurveyController.get_prototype_messages()
		channels = {message["channel"] for message in messages}
		self.assertEqual(
			channels,
			{"WhatsApp", "Correo electrónico", "Mensaje SMS", "Formulario web"},
		)
		for message in messages:
			self.assertTrue(message["message"])
			self.assertEqual(
				set(message["ratings"]),
				{"Vehículo", "Concesionario", "Vendedor"},
			)

	def test_startup_reports_missing_sales_status_migration_column(self):
		class FakeInspector:
			def get_table_names(self):
				return list(Base.metadata.tables)

			def get_columns(self, table_name):
				columns = Base.metadata.tables[table_name].columns
				return [
					{"name": column.name}
					for column in columns
					if not (
						table_name == "sales_invoice"
						and column.name == "sales_status"
					)
				]

		with patch("config.database.inspect", return_value=FakeInspector()):
			with self.assertRaisesRegex(
				RuntimeError, "sales_invoice.sales_status"
			) as error:
				init_db()
		self.assertIn("alembic upgrade head", str(error.exception))

	def test_sale_total_uses_tax_and_trade_in(self):
		subtotal, tax, total = calculate_sale_totals(
			"100.00",
			"5.00",
			{
				"trade_in": {"allowance": "10.00"},
				"customization": {"cost": "2.00"},
				"warranty": {"extended_cost": "3.00"},
			},
		)
		self.assertEqual(str(subtotal), "95.00")
		self.assertEqual(str(tax), "12.35")
		self.assertEqual(str(total), "112.35")

	def test_invalid_or_negative_sale_total_is_rejected(self):
		with self.assertRaises(ValueError):
			calculate_sale_totals("not-money", 0, {})
		with self.assertRaises(ValueError):
			calculate_sale_totals(5, 0, {"trade_in": {"allowance": 6}})

	def test_password_hash_verifies_without_storing_plaintext(self):
		password = "a-long-test-password"
		encoded = AuthController.hash_password(password)
		self.assertNotIn(password, encoded)
		self.assertTrue(AuthController.verify_password(password, encoded))
		self.assertFalse(AuthController.verify_password("wrong-password", encoded))

	def test_vehicle_status_is_not_mapped(self):
		self.assertNotIn("vehicle_status", Vehicle.__table__.c)
		self.assertIn("vehicle_delivery_mileage", Vehicle.__table__.c)

	def test_sales_invoice_constraints_compile_from_sqlalchemy_expressions(self):
		ddl = str(
			CreateTable(SalesInvoice.__table__).compile(
				dialect=postgresql.dialect()
			)
		)
		self.assertIn(
			"CHECK (sales_status IN "
			"('pending', 'approved', 'rejected', 'cancelled', 'completed'))",
			ddl,
		)
		status_constraint = next(
			constraint
			for constraint in SalesInvoice.__table__.constraints
			if constraint.name == "ck_sales_invoice_sales_status"
		)
		self.assertNotIsInstance(status_constraint.sqltext, TextClause)
		active_index = next(
			index
			for index in SalesInvoice.__table__.indexes
			if index.name == "uq_active_sales_invoice_vehicle"
		)
		index_ddl = str(
			CreateIndex(active_index).compile(dialect=postgresql.dialect())
		)
		self.assertIn(
			"WHERE sales_status IN ('pending', 'approved', 'completed')",
			index_ddl,
		)
		self.assertNotIsInstance(
			active_index.dialect_options["postgresql"]["where"], TextClause
		)

	def test_sales_approval_marks_manager_approval_and_status(self):
		class FakeInvoice:
			def __init__(self):
				self.id = 118
				self.status = "pending"
				self.manager_approval = None
				self.approved_by_employee_id = None
				self.approved_at = None
				self.rejected_by_employee_id = None
				self.rejected_at = None
				self.rejection_reason = None
				self.cancelled_by_employee_id = None
				self.cancelled_at = None
				self.cancellation_reason = None

		class FakeSupervisor:
			is_active = True
			role = "Manager"
			employee_id = 77

		class FakeScalarResult:
			def __init__(self, invoice):
				self._invoice = invoice
			def one_or_none(self):
				return self._invoice

		class FakeSession:
			def __init__(self, invoice):
				self.invoice = invoice
			def __enter__(self):
				return self
			def __exit__(self, *_):
				return False
			def scalars(self, *_args, **_kwargs):
				return FakeScalarResult(self.invoice)
			def get(self, model, value):
				return FakeSupervisor() if model.__name__ == "Employee" and value == 77 else None
			def commit(self):
				pass

		invoice = FakeInvoice()
		with patch("controllers.sales_controller.SessionLocal", return_value=FakeSession(invoice)):
			success, message = SalesController().approve_sale(118, 77)
		self.assertTrue(success)
		self.assertEqual(invoice.status, "approved")
		self.assertTrue(invoice.manager_approval)
		self.assertEqual(invoice.approved_by_employee_id, 77)
		self.assertIn("Factura 118", message)

	def test_vehicle_add_normalizes_optional_fields_and_vin(self):
		factory = FakeSession
		with patch("controllers.vehicle_controller.SessionLocal", return_value=factory()):
			success, _ = VehicleController().add_vehicle(
				{
					"vehicle_id": "1hgcm82633a004352",
					"manufacturer": "Honda",
					"model": "Accord",
					"list_price": "12000.00",
					"weight": "",
				}
			)
		self.assertTrue(success)
		self.assertEqual(factory.added.id, "1HGCM82633A004352")
		self.assertIsNone(factory.added.weight)

	def test_vehicle_add_rejects_invalid_vin_and_price(self):
		controller = VehicleController()
		invalid_vin, _ = controller.add_vehicle(
			{"vehicle_id": "short", "manufacturer": "Honda", "model": "Accord", "list_price": 1}
		)
		invalid_price, _ = controller.add_vehicle(
			{"vehicle_id": "1HGCM82633A004352", "manufacturer": "Honda", "model": "Accord", "list_price": 0}
		)
		self.assertFalse(invalid_vin)
		self.assertFalse(invalid_price)

	def test_vehicle_delete_allows_only_vehicles_without_sales(self):
		engine = create_engine("sqlite:///:memory:")
		self.addCleanup(engine.dispose)
		Base.metadata.create_all(engine)
		test_session = sessionmaker(bind=engine)
		linked_vin = "1HGCM82633A004352"
		unlinked_vin = "1HGCM82633A004360"
		with test_session() as session:
			customer = Customer(first_name="Cliente", last_name="Prueba")
			employee = Employee(
				first_name="Vendedor", last_name="Prueba", role="Salesperson"
			)
			linked_vehicle = Vehicle(
				id=linked_vin,
				manufacturer="Honda",
				model="Accord",
				list_price=Decimal("12000"),
			)
			unlinked_vehicle = Vehicle(
				id=unlinked_vin,
				manufacturer="Honda",
				model="Civic",
				list_price=Decimal("10000"),
			)
			session.add_all([customer, employee, linked_vehicle, unlinked_vehicle])
			session.flush()
			session.add(
				SalesInvoice(
					customer_id=customer.id,
					employee_id=employee.employee_id,
					vehicle_id=linked_vin,
					current_mileage=10,
					negotiated_price=Decimal("12000"),
					manager_approval=True,
					tax_amount=Decimal("780"),
					license_fee_amount=Decimal("0"),
					total_amount=Decimal("12780"),
					status="completed",
				)
			)
			session.commit()

		with patch("controllers.vehicle_controller.SessionLocal", test_session):
			success, message = VehicleController().delete_vehicle(unlinked_vin)
			self.assertTrue(success, message)
			success, message = VehicleController().delete_vehicle(linked_vin)
			self.assertFalse(success)
			self.assertIn("ventas asociadas", message)
			success, message = VehicleController().delete_vehicle("VIN inválido")
			self.assertFalse(success)

		with test_session() as session:
			self.assertIsNotNone(session.get(Vehicle, linked_vin))
			self.assertIsNone(session.get(Vehicle, unlinked_vin))


if __name__ == "__main__":
	unittest.main()