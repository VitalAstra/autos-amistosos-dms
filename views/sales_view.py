from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from PySide6.QtCore import QLocale, Signal
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
	QCheckBox,
	QComboBox,
	QDoubleSpinBox,
	QFormLayout,
	QFrame,
	QHBoxLayout,
	QLabel,
	QLineEdit,
	QMessageBox,
	QPushButton,
	QSpinBox,
	QStackedWidget,
	QVBoxLayout,
	QWidget,
)


class SalesView(QWidget):
	"""Asistente de tres pasos para preparar una factura de venta."""

	sale_requested = Signal(dict)

	_TAX_RATE = Decimal("0.13")
	_CENT = Decimal("0.01")

	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("Nueva venta")

		main_layout = QVBoxLayout(self)
		main_layout.setContentsMargins(0, 0, 0, 0)
		main_layout.setSpacing(12)

		self.step_indicator = QLabel()
		self.step_indicator.setObjectName("viewTitle")
		main_layout.addWidget(self.step_indicator)

		self.step_stack = QStackedWidget()
		self.step_stack.addWidget(self._build_selection_step())
		self.step_stack.addWidget(self._build_addons_step())
		self.step_stack.addWidget(self._build_summary_step())
		main_layout.addWidget(self.step_stack, 1)

		navigation_layout = QHBoxLayout()
		self.back_button = QPushButton("Anterior")
		self.next_button = QPushButton("Continuar")
		self.process_button = QPushButton("Procesar Factura de Venta")
		self.process_button.setObjectName("primaryButton")
		self.back_button.clicked.connect(self._go_back)
		self.next_button.clicked.connect(self._go_forward)
		self.process_button.clicked.connect(self._submit_sale)
		navigation_layout.addWidget(self.back_button)
		navigation_layout.addStretch(1)
		navigation_layout.addWidget(self.next_button)
		navigation_layout.addWidget(self.process_button)
		main_layout.addLayout(navigation_layout)

		self._set_step(0)
		self._refresh_totals()

	def load_selection_data(self, customers, vehicles):
		"""Carga las opciones de cliente y vehículo en los selectores."""
		self._vehicles_by_id = {}
		self.customer_combo.clear()
		self.customer_combo.addItem("Seleccionar cliente", None)
		for customer in customers:
			customer_id = self._get_value(customer, "id")
			if customer_id is None:
				customer_id = self._get_value(customer, "customer_id")
			first_name = self._get_value(customer, "first_name")
			if first_name is None:
				first_name = self._get_value(customer, "customer_first_name")
			last_name = self._get_value(customer, "last_name")
			if last_name is None:
				last_name = self._get_value(customer, "customer_last_name")
			full_name = f"{first_name or ''} {last_name or ''}".strip()
			self.customer_combo.addItem(full_name or str(customer_id), customer_id)

		self.vehicle_combo.clear()
		self.vehicle_combo.addItem("Seleccionar vehículo", None)
		for vehicle in vehicles:
			vehicle_id = self._get_value(vehicle, "id")
			if vehicle_id is None:
				vehicle_id = self._get_value(vehicle, "vehicle_id")
			if vehicle_id is None:
				continue
			self._vehicles_by_id[str(vehicle_id)] = vehicle
			manufacturer = self._get_value(vehicle, "manufacturer") or ""
			model = self._get_value(vehicle, "model") or ""
			description = " ".join(
				part for part in (str(manufacturer), str(model)) if part
			)
			label = f"{description} ({vehicle_id})" if description else str(vehicle_id)
			self.vehicle_combo.addItem(label, vehicle_id)

		self._update_price_from_vehicle()

	def get_sale_payload(self):
		"""Retorna la selección, los complementos y los totales de la venta."""
		if self.customer_combo.currentData() is None:
			raise ValueError("Selecciona un cliente.")
		if self.vehicle_combo.currentData() is None:
			raise ValueError("Selecciona un vehículo.")

		negotiated_price = self._read_amount(
			self.negotiated_price_input.text(), "El precio negociado"
		)
		license_fee = self.plate_fee_input.value_decimal()
		addons = self._get_addons_payload()
		subtotal = (
			negotiated_price
			+ (addons["insurance"] or {}).get("premium", Decimal("0"))
			+ (addons["warranty"] or {}).get("price", Decimal("0"))
			- (addons["trade_in"] or {}).get("value", Decimal("0"))
		)
		if subtotal < 0:
			raise ValueError("El subtotal no puede ser negativo.")

		tax_amount = (subtotal * self._TAX_RATE).quantize(
			self._CENT, rounding=ROUND_HALF_UP
		)
		total_amount = subtotal + tax_amount + license_fee
		return {
			"customer_id": self.customer_combo.currentData(),
			"vehicle_id": self.vehicle_combo.currentData(),
			"sales_negotiated_price": negotiated_price,
			"sales_tax_amount": tax_amount,
			"sales_license_fee_amount": license_fee,
			"sales_total_amount": total_amount,
			"addons": addons,
		}

	def _build_selection_step(self):
		page = self._create_step_card("Selección de cliente y vehículo")
		layout = page.layout()
		form = QFormLayout()
		form.setVerticalSpacing(12)
		form.setHorizontalSpacing(16)

		self.customer_combo = QComboBox()
		self.customer_combo.addItem("Seleccionar cliente", None)
		self.vehicle_combo = QComboBox()
		self.vehicle_combo.addItem("Seleccionar vehículo", None)
		self.negotiated_price_input = QLineEdit()
		self.negotiated_price_input.setPlaceholderText("0.00")
		self.negotiated_price_input.setValidator(
			QDoubleValidator(0, 999999999, 2, self.negotiated_price_input)
		)
		self.negotiated_price_input.validator().setLocale(QLocale.c())
		self.negotiated_price_input.textChanged.connect(self._refresh_totals)
		self.vehicle_combo.currentIndexChanged.connect(
			self._update_price_from_vehicle
		)

		form.addRow("Cliente", self.customer_combo)
		form.addRow("Vehículo", self.vehicle_combo)
		form.addRow("Precio negociado", self.negotiated_price_input)
		layout.addLayout(form)
		layout.addStretch(1)
		return page

	def _build_addons_step(self):
		page = self._create_step_card("Adicionales de la venta")
		layout = page.layout()
		self.trade_in_checkbox = QCheckBox("Incluye Trade-In")
		self.financing_checkbox = QCheckBox("Requiere Financiamiento")
		self.insurance_checkbox = QCheckBox("Seguro Incluido")
		self.warranty_checkbox = QCheckBox("Garantía Extendida")

		self.trade_in_description_input = QLineEdit()
		self.trade_in_value_input = self._create_money_input()
		self.trade_in_fields = self._create_addon_fields(
			("Vehículo recibido", self.trade_in_description_input),
			("Valor del Trade-In", self.trade_in_value_input),
		)
		self.financing_lender_input = QLineEdit()
		self.financing_term_input = self._create_integer_input(1, 600)
		self.financing_down_payment_input = self._create_money_input()
		self.financing_fields = self._create_addon_fields(
			("Entidad financiera", self.financing_lender_input),
			("Plazo (meses)", self.financing_term_input),
			("Prima inicial", self.financing_down_payment_input),
		)
		self.insurance_provider_input = QLineEdit()
		self.insurance_premium_input = self._create_money_input()
		self.insurance_fields = self._create_addon_fields(
			("Aseguradora", self.insurance_provider_input),
			("Prima del seguro", self.insurance_premium_input),
		)
		self.warranty_coverage_input = QLineEdit()
		self.warranty_duration_input = self._create_integer_input(1, 600)
		self.warranty_price_input = self._create_money_input()
		self.warranty_fields = self._create_addon_fields(
			("Cobertura", self.warranty_coverage_input),
			("Duración (meses)", self.warranty_duration_input),
			("Precio de garantía", self.warranty_price_input),
		)

		for checkbox, fields in (
			(self.trade_in_checkbox, self.trade_in_fields),
			(self.financing_checkbox, self.financing_fields),
			(self.insurance_checkbox, self.insurance_fields),
			(self.warranty_checkbox, self.warranty_fields),
		):
			layout.addWidget(checkbox)
			layout.addWidget(fields)
			fields.setVisible(False)
			checkbox.toggled.connect(fields.setVisible)
			checkbox.toggled.connect(self._refresh_totals)

		for field in (
			self.trade_in_value_input,
			self.insurance_premium_input,
			self.warranty_price_input,
		):
			field.valueChanged.connect(self._refresh_totals)

		layout.addStretch(1)
		return page

	def _build_summary_step(self):
		page = self._create_step_card("Resumen y totales")
		layout = page.layout()
		self.subtotal_label = self._create_total_label()
		self.tax_label = self._create_total_label()
		self.plates_label = self._create_total_label()
		self.final_total_label = self._create_total_label()
		totals_layout = QFormLayout()
		totals_layout.setVerticalSpacing(14)
		totals_layout.addRow("Subtotal", self.subtotal_label)
		totals_layout.addRow("Impuestos (13%)", self.tax_label)

		self.plate_fee_input = self._create_money_input()
		self.plate_fee_input.valueChanged.connect(self._refresh_totals)
		totals_layout.addRow("Placas", self.plates_label)
		totals_layout.addRow("Costo de placas", self.plate_fee_input)
		totals_layout.addRow("Total Final", self.final_total_label)
		layout.addLayout(totals_layout)
		layout.addStretch(1)
		return page

	@staticmethod
	def _create_step_card(title):
		card = QFrame()
		card.setObjectName("card")
		layout = QVBoxLayout(card)
		layout.setContentsMargins(20, 20, 20, 20)
		layout.setSpacing(16)
		title_label = QLabel(title)
		title_label.setObjectName("viewTitle")
		layout.addWidget(title_label)
		return card

	@staticmethod
	def _create_addon_fields(*fields):
		container = QWidget()
		form = QFormLayout(container)
		form.setContentsMargins(16, 0, 0, 8)
		form.setVerticalSpacing(8)
		for label, field in fields:
			form.addRow(label, field)
		return container

	@staticmethod
	def _create_money_input():
		input_field = SalesView._MoneyInput()
		input_field.setRange(0, 999999999)
		input_field.setDecimals(2)
		input_field.setSingleStep(100)
		input_field.setPrefix("$ ")
		return input_field

	@staticmethod
	def _create_integer_input(minimum, maximum):
		input_field = QSpinBox()
		input_field.setRange(minimum, maximum)
		return input_field

	@staticmethod
	def _create_total_label():
		label = QLabel("$0.00")
		label.setObjectName("totalValue")
		return label

	def _create_addon_payload(self, enabled, values):
		if not enabled:
			return None
		return values

	def _get_addons_payload(self):
		return {
			"trade_in": self._create_addon_payload(
				self.trade_in_checkbox.isChecked(),
				{
					"vehicle_description": self.trade_in_description_input.text().strip(),
					"value": self.trade_in_value_input.value_decimal(),
				},
			),
			"financing": self._create_addon_payload(
				self.financing_checkbox.isChecked(),
				{
					"lender": self.financing_lender_input.text().strip(),
					"term_months": self.financing_term_input.value(),
					"down_payment": self.financing_down_payment_input.value_decimal(),
				},
			),
			"insurance": self._create_addon_payload(
				self.insurance_checkbox.isChecked(),
				{
					"provider": self.insurance_provider_input.text().strip(),
					"premium": self.insurance_premium_input.value_decimal(),
				},
			),
			"warranty": self._create_addon_payload(
				self.warranty_checkbox.isChecked(),
				{
					"coverage": self.warranty_coverage_input.text().strip(),
					"duration_months": self.warranty_duration_input.value(),
					"price": self.warranty_price_input.value_decimal(),
				},
			),
		}

	def _set_step(self, step_index):
		self.step_stack.setCurrentIndex(step_index)
		self.step_indicator.setText(f"Paso {step_index + 1} de 3")
		self.back_button.setEnabled(step_index > 0)
		self.next_button.setVisible(step_index < 2)
		self.process_button.setVisible(step_index == 2)
		if step_index == 2:
			self._refresh_totals()

	def _go_back(self):
		self._set_step(max(0, self.step_stack.currentIndex() - 1))

	def _go_forward(self):
		if self.step_stack.currentIndex() == 0:
			if self.customer_combo.currentData() is None:
				QMessageBox.warning(self, "Datos incompletos", "Selecciona un cliente.")
				return
			if self.vehicle_combo.currentData() is None:
				QMessageBox.warning(self, "Datos incompletos", "Selecciona un vehículo.")
				return
			try:
				self._read_amount(
					self.negotiated_price_input.text(), "El precio negociado"
				)
			except ValueError as error:
				QMessageBox.warning(self, "Precio no válido", str(error))
				self.negotiated_price_input.setFocus()
				return
		self._set_step(min(2, self.step_stack.currentIndex() + 1))

	def _submit_sale(self):
		try:
			payload = self.get_sale_payload()
		except ValueError as error:
			QMessageBox.warning(self, "Datos incompletos", str(error))
			return
		self.sale_requested.emit(payload)

	def _refresh_totals(self, *_):
		try:
			negotiated_price = self._read_amount(
				self.negotiated_price_input.text(), "El precio negociado"
			)
			addons = self._get_addons_payload()
			subtotal = (
				negotiated_price
				+ (addons["insurance"] or {}).get("premium", Decimal("0"))
				+ (addons["warranty"] or {}).get("price", Decimal("0"))
				- (addons["trade_in"] or {}).get("value", Decimal("0"))
			)
			if subtotal < 0:
				raise ValueError("El subtotal no puede ser negativo.")
			tax_amount = (subtotal * self._TAX_RATE).quantize(
				self._CENT, rounding=ROUND_HALF_UP
			)
			license_fee = self.plate_fee_input.value_decimal()
		except (InvalidOperation, ValueError):
			for label in (
				self.subtotal_label,
				self.tax_label,
				self.final_total_label,
			):
				label.setText("—")
			return

		self.subtotal_label.setText(self._format_money(subtotal))
		self.tax_label.setText(self._format_money(tax_amount))
		self.plates_label.setText(self._format_money(license_fee))
		self.final_total_label.setText(
			self._format_money(subtotal + tax_amount + license_fee)
		)

	def _update_price_from_vehicle(self, *_):
		vehicle_id = self.vehicle_combo.currentData()
		if vehicle_id is None:
			return
		vehicle = self._vehicles_by_id.get(str(vehicle_id))
		if vehicle is None:
			return
		price = self._get_value(vehicle, "list_price")
		if price is not None:
			self.negotiated_price_input.setText(str(price))

	@staticmethod
	def _get_value(item, key):
		if isinstance(item, dict):
			return item.get(key)
		return getattr(item, key, None)

	@staticmethod
	def _read_amount(text, label):
		try:
			amount = Decimal(text.strip())
		except (InvalidOperation, ValueError):
			raise ValueError(f"{label} debe ser un número válido.")
		if not amount.is_finite() or amount < 0:
			raise ValueError(f"{label} debe ser un monto no negativo.")
		return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

	@staticmethod
	def _format_money(amount):
		return f"${amount:,.2f}"

	class _MoneyInput(QDoubleSpinBox):
		"""Campo monetario que conserva precisión decimal en el payload."""

		def value_decimal(self):
			return Decimal(str(self.value())).quantize(Decimal("0.01"))
