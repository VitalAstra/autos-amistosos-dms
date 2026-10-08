from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from psycopg import sql

from config.database import DatabaseConnection


class SalesController:
	"""Procesa ventas y sus complementos dentro de una transacción."""

	_ADDON_TABLES = {
		"financing": "sales_financing",
		"trade_in": "sales_trade_in",
		"customization": "sales_customization",
		"insurance": "sales_insurance",
		"warranty": "sales_warranty",
	}

	def process_sale(self, invoice_data, addons_data):
		"""Guarda una factura y sus complementos de forma atómica."""
		conn = None
		try:
			conn = DatabaseConnection.get_connection()
			negotiated_price = Decimal(str(invoice_data["sales_negotiated_price"]))
			license_fee = Decimal(str(invoice_data.get("sales_license_fee_amount", 0)))
			if not negotiated_price.is_finite() or not license_fee.is_finite():
				raise ValueError("Los montos de la venta deben ser números finitos.")

			sales_tax_amount = (negotiated_price * Decimal("0.13")).quantize(
				Decimal("0.01"), rounding=ROUND_HALF_UP
			)
			sales_total_amount = negotiated_price + sales_tax_amount + license_fee

			with conn.cursor() as cursor:
				cursor.execute(
					"""
					INSERT INTO sales_invoice (
						sales_date, customer_id, employee_id, vehicle_id,
						sales_current_mileage, sales_negotiated_price,
						sales_manager_approval, sales_tax_amount,
						sales_license_fee_amount, sales_total_amount
					)
					VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
					RETURNING sales_invoice_number
					""",
					(
						invoice_data["sales_date"],
						invoice_data["customer_id"],
						invoice_data["employee_id"],
						invoice_data["vehicle_id"],
						invoice_data.get("sales_current_mileage"),
						negotiated_price,
						invoice_data.get("sales_manager_approval"),
						sales_tax_amount,
						license_fee,
						sales_total_amount,
					),
				)
				invoice_number = cursor.fetchone()["sales_invoice_number"]

				for addon_name, table_name in self._ADDON_TABLES.items():
					if addon_name not in addons_data or addons_data[addon_name] is None:
						continue

					addon_fields = addons_data[addon_name]
					if not isinstance(addon_fields, dict):
						raise TypeError(
							f"Los datos de {addon_name} deben ser un diccionario."
						)

					addon_fields = {
						field: value
						for field, value in addon_fields.items()
						if field != "sales_invoice_number"
					}
					columns = ["sales_invoice_number", *addon_fields.keys()]
					values = [invoice_number, *addon_fields.values()]
					insert_addon = sql.SQL(
						"INSERT INTO {} ({}) VALUES ({})"
					).format(
						sql.Identifier(table_name),
						sql.SQL(", ").join(sql.Identifier(column) for column in columns),
						sql.SQL(", ").join(sql.Placeholder() for _ in values),
					)
					cursor.execute(insert_addon, tuple(values))

			conn.commit()
			return True, f"Venta registrada con factura {invoice_number}."
		except Exception as error:
			if conn is not None:
				try:
					conn.rollback()
				except Exception:
					pass
			return False, str(error)
		finally:
			if conn is not None:
				conn.close()
