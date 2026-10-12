from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


TAX_RATE = Decimal("0.13")
CENT = Decimal("0.01")


def calculate_sale_totals(negotiated_price, license_fee, addons):
	"""Calcula subtotal gravable, impuesto del 13% y total en USD."""
	price = _money(negotiated_price, "El precio negociado")
	fee = _money(license_fee, "La tarifa de placas")
	trade_in = addons.get("trade_in") or {}
	customization = addons.get("customization") or {}
	warranty = addons.get("warranty") or {}

	subtotal = (
		price
		+ _money(customization.get("cost", 0), "El costo de personalización")
		+ _money(warranty.get("extended_cost", 0), "El costo de garantía")
		- _money(trade_in.get("allowance", 0), "El valor del trade-in")
	)
	if subtotal < 0:
		raise ValueError("El subtotal no puede ser negativo.")

	tax_amount = (subtotal * TAX_RATE).quantize(CENT, rounding=ROUND_HALF_UP)
	total_amount = subtotal + tax_amount + fee
	return subtotal, tax_amount, total_amount


def _money(value, label):
	try:
		amount = Decimal(str(value))
	except (InvalidOperation, TypeError, ValueError) as error:
		raise ValueError(f"{label} debe ser un número válido.") from error
	if not amount.is_finite() or amount < 0:
		raise ValueError(f"{label} debe ser un monto no negativo.")
	return amount.quantize(CENT, rounding=ROUND_HALF_UP)