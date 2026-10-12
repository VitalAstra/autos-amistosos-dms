import unittest
from unittest.mock import patch

from controllers.auth_controller import AuthController
from controllers.sales_controller import SalesController
from controllers.vehicle_controller import VehicleController
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


if __name__ == "__main__":
	unittest.main()