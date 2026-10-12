from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from PySide6.QtCore import QEvent, QLocale, Qt, Signal
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
	QCheckBox,
	QComboBox,
	QCompleter,
	QDoubleSpinBox,
	QFormLayout,
	QFrame,
	QHBoxLayout,
	QLabel,
	QLineEdit,
	QMessageBox,
	QPushButton,
	QScrollArea,
	QSpinBox,
	QStackedWidget,
	QVBoxLayout,
	QWidget,
)

from config.settings import SALES_TAX_RATE
from utils.validators import set_vin_validator


class SalesView(QWidget):
	"""Asistente de venta conectado a los datos y restricciones de PostgreSQL."""

	sale_requested = Signal(dict)

	_CENT = Decimal("0.01")

	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("Nueva venta")
		self._vehicles_by_id = {}

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

	def load_selection_data(self, customers, vehicles, employees):
		"""Carga clientes, vehículos disponibles y empleados existentes."""
		self._vehicles_by_id = {}
		self.customer_combo.clear()
		self._customers_by_id = {}
		for customer in customers:
			label = f"{customer.first_name} {customer.last_name}".strip()
			self._customers_by_id[customer.id] = customer
			self.customer_combo.addItem(label, customer.id)
		self._configure_searchable_combo(
			self.customer_combo, "Seleccionar cliente"
		)

		self.vehicle_combo.clear()
		for vehicle in vehicles:
			self._vehicles_by_id[vehicle.id] = vehicle
			description = " ".join(
				part
				for part in (vehicle.manufacturer, vehicle.model)
				if part
			)
			label = (
				f"{description} ({vehicle.id})"
				if description
				else vehicle.id
			)
			self.vehicle_combo.addItem(label, vehicle.id)
		self._configure_searchable_combo(
			self.vehicle_combo, "Seleccionar vehículo"
		)

		self.employee_combo.clear()
		for employee in employees:
			name = f"{employee.first_name} {employee.last_name}".strip()
			label = f"{name} — {employee.role}"
			self.employee_combo.addItem(label, employee.employee_id)
		self._configure_searchable_combo(
			self.employee_combo, "Seleccionar empleado"
		)
		self._update_price_from_vehicle()

	@staticmethod
	def _configure_searchable_combo(combo, placeholder):
		"""Configura el autocompletado y evita seleccionar el primer registro."""
		combo.setCurrentIndex(-1)
		combo.clearEditText()
		combo.lineEdit().setPlaceholderText(placeholder)

		completer = QCompleter(combo.model(), combo)
		completer.setCompletionRole(Qt.ItemDataRole.DisplayRole)
		completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
		completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
		completer.setFilterMode(Qt.MatchFlag.MatchContains)
		completer.activated[str].connect(
			lambda text: SalesView._select_combo_completion(combo, text)
		)
		combo.setCompleter(completer)

	@staticmethod
	def _select_combo_completion(combo, text):
		index = combo.findText(text, Qt.MatchFlag.MatchExactly)
		if index >= 0:
			combo.setCurrentIndex(index)

	def get_sale_payload(self):
		"""Construye y valida todos los datos necesarios para procesar la venta."""
		customer_id = self.customer_combo.currentData()
		vehicle_id = self.vehicle_combo.currentData()
		employee_id = self.employee_combo.currentData()
		if customer_id is None:
			raise ValueError("Selecciona un cliente.")
		if vehicle_id is None:
			raise ValueError("Selecciona un vehículo disponible.")
		if employee_id is None:
			raise ValueError("Selecciona el empleado responsable de la venta.")

		negotiated_price = self._read_amount(
			self.negotiated_price_input.text(), "El precio negociado"
		)
		addons = self._get_addons_payload()
		license_fee = self.plate_fee_input.value_decimal()
		subtotal = self._calculate_subtotal(negotiated_price, addons)
		tax_amount = self._calculate_tax(subtotal)
		return {
			"customer_id": customer_id,
			"vehicle_id": vehicle_id,
			"employee_id": employee_id,
			"current_mileage": self.current_mileage_input.value(),
			"negotiated_price": negotiated_price,
			"tax_rate": SALES_TAX_RATE,
			"license_fee": license_fee,
			"addons": addons,
			"manager_approval": None,
			"subtotal": subtotal,
			"tax_amount": tax_amount,
			"total_amount": subtotal + tax_amount + license_fee,
		}

	def show_sale_result(self, success, message):
		"""Muestra el resultado del procesamiento y prepara otra venta si se guardó."""
		if success:
			QMessageBox.information(self, "Venta registrada", message)
			self._reset_form()
		else:
			QMessageBox.critical(self, "No se pudo registrar la venta", message)

	def _build_selection_step(self):
		page = self._create_step_card("Selección de cliente y vehículo")
		layout = page.layout()
		form = QFormLayout()
		form.setVerticalSpacing(12)
		form.setHorizontalSpacing(16)

		self.customer_combo = QComboBox()
		# Hacer el combobox editable y con autocompletado para búsqueda rápida
		self.customer_combo.setEditable(True)
		self.customer_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
		# Usar placeholder en el LineEdit del combo en lugar de un ítem real
		try:
			self.customer_combo.setCurrentIndex(-1)
		except Exception:
			pass
		line_edit = self.customer_combo.lineEdit()
		line_edit.setPlaceholderText("Seleccionar cliente")
		line_edit.installEventFilter(self)
		self.vehicle_combo = QComboBox()
		# Hacer editable para permitir placeholder y búsqueda rápida
		self.vehicle_combo.setEditable(True)
		self.vehicle_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
		try:
			self.vehicle_combo.setCurrentIndex(-1)
		except Exception:
			pass
		vehicle_le = self.vehicle_combo.lineEdit()
		vehicle_le.setPlaceholderText("Seleccionar vehículo")
		vehicle_le.installEventFilter(self)
		self.employee_combo = QComboBox()
		# Hacer editable para placeholder y búsqueda por empleado
		self.employee_combo.setEditable(True)
		self.employee_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
		try:
			self.employee_combo.setCurrentIndex(-1)
		except Exception:
			pass
		emp_le = self.employee_combo.lineEdit()
		emp_le.setPlaceholderText("Seleccionar empleado")
		emp_le.installEventFilter(self)
		self.negotiated_price_input = QLineEdit()
		self.negotiated_price_input.setPlaceholderText("Precio negociado")
		validator = QDoubleValidator(
			0, 999999999, 2, self.negotiated_price_input
		)
		validator.setLocale(QLocale.c())
		self.negotiated_price_input.setValidator(validator)
		self.negotiated_price_input.textChanged.connect(self._refresh_totals)
		self.current_mileage_input = QSpinBox()
		self.current_mileage_input.setRange(0, 2_000_000)
		self.current_mileage_input.setGroupSeparatorShown(True)
		self.vehicle_combo.currentIndexChanged.connect(
			self._update_price_from_vehicle
		)

		form.addRow("Cliente", self.customer_combo)
		form.addRow("Vehículo disponible", self.vehicle_combo)
		form.addRow("Empleado responsable", self.employee_combo)
		form.addRow("Precio negociado", self.negotiated_price_input)
		form.addRow("Kilometraje actual", self.current_mileage_input)
		layout.addLayout(form)
		layout.addStretch(1)
		return page

	def _build_addons_step(self):
		page = self._create_step_card("Adicionales de la venta")
		page_layout = page.layout()
		scroll_area = QScrollArea()
		scroll_area.setWidgetResizable(True)
		scroll_area.setFrameShape(QFrame.Shape.NoFrame)
		addons_container = QWidget()
		layout = QVBoxLayout(addons_container)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(8)

		self.trade_in_checkbox = QCheckBox("Incluye Trade-In")
		self.trade_in_description_input = QLineEdit()
		self.trade_in_description_input.setPlaceholderText("VIN de 17 caracteres")
		set_vin_validator(self.trade_in_description_input)
		self.trade_in_value_input = self._create_money_input()
		self.trade_in_fields = self._create_addon_fields(
			("VIN del vehículo recibido", self.trade_in_description_input),
			("Valor de Trade-In", self.trade_in_value_input),
		)

		self.financing_checkbox = QCheckBox("Requiere Financiamiento")
		self.financing_source_input = QLineEdit()
		self.financing_source_input.setPlaceholderText(
			"Fuente del financiamiento"
		)
		self.financing_bank_input = QLineEdit()
		self.financing_bank_input.setPlaceholderText("Banco")
		self.financing_fields = self._create_addon_fields(
			("Fuente de financiamiento", self.financing_source_input),
			("Banco", self.financing_bank_input),
		)

		self.insurance_checkbox = QCheckBox("Seguro Incluido")
		self.insurance_company_input = QLineEdit()
		self.insurance_company_input.setPlaceholderText("Aseguradora")
		self.insurance_policy_input = QLineEdit()
		self.insurance_policy_input.setPlaceholderText("Número de póliza")
		self.insurance_proof_checkbox = QCheckBox("Comprobante presentado")
		self.insurance_fields = self._create_addon_fields(
			("Aseguradora", self.insurance_company_input),
			("Número de póliza", self.insurance_policy_input),
			("Comprobante", self.insurance_proof_checkbox),
		)

		self.warranty_checkbox = QCheckBox("Garantía Extendida")
		self.warranty_type_input = QLineEdit()
		self.warranty_type_input.setPlaceholderText("Tipo de garantía")
		self.warranty_cost_input = self._create_money_input()
		self.warranty_fields = self._create_addon_fields(
			("Tipo de garantía", self.warranty_type_input),
			("Costo extendido", self.warranty_cost_input),
		)

		self.customization_checkbox = QCheckBox("Personalización")
		self.customization_type_input = QLineEdit()
		self.customization_type_input.setPlaceholderText(
			"Tipo de personalización"
		)
		self.customization_cost_input = self._create_money_input()
		self.customization_fields = self._create_addon_fields(
			("Tipo de personalización", self.customization_type_input),
			("Costo", self.customization_cost_input),
		)

		for checkbox, fields in (
			(self.trade_in_checkbox, self.trade_in_fields),
			(self.financing_checkbox, self.financing_fields),
			(self.insurance_checkbox, self.insurance_fields),
			(self.warranty_checkbox, self.warranty_fields),
			(self.customization_checkbox, self.customization_fields),
		):
			layout.addWidget(checkbox)
			layout.addWidget(fields)
			fields.setVisible(False)
			checkbox.toggled.connect(fields.setVisible)
			checkbox.toggled.connect(self._refresh_totals)
		for field in (
			self.trade_in_value_input,
			self.warranty_cost_input,
			self.customization_cost_input,
		):
			field.valueChanged.connect(self._refresh_totals)
		layout.addStretch(1)
		scroll_area.setWidget(addons_container)
		page_layout.addWidget(scroll_area, 1)
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
		totals_layout.addRow(
			f"Impuestos ({SALES_TAX_RATE * 100:g}%)", self.tax_label
		)
		self.plate_fee_input = self._create_money_input()
		self.plate_fee_input.valueChanged.connect(self._refresh_totals)
		totals_layout.addRow("Costo de placas", self.plate_fee_input)
		totals_layout.addRow("Placas", self.plates_label)
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

	def eventFilter(self, obj, event):
		"""Limpia el placeholder al enfocar cualquier selector de la venta."""
		combo_placeholders = {
			self.customer_combo.lineEdit(): (
				self.customer_combo, "Seleccionar cliente"
			),
			self.vehicle_combo.lineEdit(): (
				self.vehicle_combo, "Seleccionar vehículo"
			),
			self.employee_combo.lineEdit(): (
				self.employee_combo, "Seleccionar empleado"
			),
		}
		if obj in combo_placeholders:
			combo, placeholder = combo_placeholders[obj]
			if event.type() == QEvent.FocusIn:
				obj.setPlaceholderText("")
			elif event.type() == QEvent.FocusOut:
				if combo.currentIndex() < 0 and not obj.text():
					obj.setPlaceholderText(placeholder)
		return super().eventFilter(obj, event)

	@staticmethod
	def _create_total_label():
		label = QLabel("$0.00")
		label.setObjectName("totalValue")
		return label

	def _get_addons_payload(self):
		addons = {
			"trade_in": None,
			"financing": None,
			"insurance": None,
			"warranty": None,
			"customization": None,
		}
		if self.trade_in_checkbox.isChecked():
			old_vehicle_id = self.trade_in_description_input.text().strip().upper()
			if len(old_vehicle_id) != 17:
				raise ValueError("El VIN del Trade-In debe tener 17 caracteres.")
			addons["trade_in"] = {
				"old_vehicle_id": old_vehicle_id,
				"allowance": self.trade_in_value_input.value_decimal(),
			}
		if self.financing_checkbox.isChecked():
			source = self.financing_source_input.text().strip()
			if not source:
				raise ValueError("Indica la fuente del financiamiento.")
			addons["financing"] = {
				"source": source,
				"bank_name": self.financing_bank_input.text().strip() or None,
			}
		if self.insurance_checkbox.isChecked():
			company = self.insurance_company_input.text().strip()
			policy_number = self.insurance_policy_input.text().strip()
			if not company or not policy_number:
				raise ValueError("Indica la aseguradora y el número de póliza.")
			addons["insurance"] = {
				"company": company,
				"policy_number": policy_number,
				"proof_submitted": self.insurance_proof_checkbox.isChecked(),
			}
		if self.warranty_checkbox.isChecked():
			warranty_type = self.warranty_type_input.text().strip()
			if not warranty_type:
				raise ValueError("Indica el tipo de garantía.")
			addons["warranty"] = {
				"type": warranty_type,
				"extended_cost": self.warranty_cost_input.value_decimal(),
			}
		if self.customization_checkbox.isChecked():
			customization_type = self.customization_type_input.text().strip()
			if not customization_type:
				raise ValueError("Indica el tipo de personalización.")
			addons["customization"] = {
				"type": customization_type,
				"cost": self.customization_cost_input.value_decimal(),
			}
		return addons

	@classmethod
	def _calculate_subtotal(cls, negotiated_price, addons):
		trade_in = addons["trade_in"]
		warranty = addons["warranty"]
		customization = addons["customization"]
		subtotal = negotiated_price
		if warranty:
			subtotal += warranty["extended_cost"]
		if customization:
			subtotal += customization["cost"]
		if trade_in:
			subtotal -= trade_in["allowance"]
		if subtotal < 0:
			raise ValueError("El subtotal no puede ser negativo.")
		return subtotal.quantize(cls._CENT, rounding=ROUND_HALF_UP)

	@classmethod
	def _calculate_tax(cls, subtotal):
		return (subtotal * SALES_TAX_RATE).quantize(
			cls._CENT, rounding=ROUND_HALF_UP
		)

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
		try:
			if self.step_stack.currentIndex() == 0:
				self._validate_selection()
			elif self.step_stack.currentIndex() == 1:
				self._get_addons_payload()
		except ValueError as error:
			QMessageBox.warning(self, "Datos incompletos", str(error))
			return
		self._set_step(min(2, self.step_stack.currentIndex() + 1))

	def _validate_selection(self):
		if self.customer_combo.currentData() is None:
			raise ValueError("Selecciona un cliente.")
		if self.vehicle_combo.currentData() is None:
			raise ValueError("Selecciona un vehículo disponible.")
		if self.employee_combo.currentData() is None:
			raise ValueError("Selecciona el empleado responsable.")
		self._read_amount(self.negotiated_price_input.text(), "El precio negociado")

	def _submit_sale(self):
		try:
			payload = self.get_sale_payload()
		except ValueError as error:
			QMessageBox.warning(self, "Datos incompletos", str(error))
			return
		self.sale_requested.emit(payload)

	def _refresh_totals(self, *_):
		try:
			price = self._read_amount(
				self.negotiated_price_input.text(), "El precio negociado"
			)
			addons = self._get_addons_payload()
			subtotal = self._calculate_subtotal(price, addons)
			tax_amount = self._calculate_tax(subtotal)
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
			self.negotiated_price_input.clear()
			return
		vehicle = self._vehicles_by_id.get(str(vehicle_id))
		if vehicle is not None and vehicle.list_price is not None:
			self.negotiated_price_input.setText(str(vehicle.list_price))

	def _reset_form(self):
		self._set_step(0)
		for combo, placeholder in (
			(self.customer_combo, "Seleccionar cliente"),
			(self.vehicle_combo, "Seleccionar vehículo"),
			(self.employee_combo, "Seleccionar empleado"),
		):
			combo.setCurrentIndex(-1)
			combo.clearEditText()
			combo.lineEdit().setPlaceholderText(placeholder)
		self.current_mileage_input.setValue(0)
		self.plate_fee_input.setValue(0)
		for checkbox in (
			self.trade_in_checkbox,
			self.financing_checkbox,
			self.insurance_checkbox,
			self.warranty_checkbox,
			self.customization_checkbox,
		):
			checkbox.setChecked(False)
		for field in (
			self.trade_in_description_input,
			self.financing_source_input,
			self.financing_bank_input,
			self.insurance_company_input,
			self.insurance_policy_input,
			self.warranty_type_input,
			self.customization_type_input,
			self.negotiated_price_input,
		):
			field.clear()
		for field in (
			self.trade_in_value_input,
			self.warranty_cost_input,
			self.customization_cost_input,
		):
			field.setValue(0)
		self.insurance_proof_checkbox.setChecked(False)

	@staticmethod
	def _read_amount(text, label):
		try:
			amount = Decimal(text.strip())
		except (InvalidOperation, ValueError) as error:
			raise ValueError(f"{label} debe ser un número válido.") from error
		if not amount.is_finite() or amount < 0:
			raise ValueError(f"{label} debe ser un monto no negativo.")
		return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

	@staticmethod
	def _format_money(amount):
		return f"${amount:,.2f}"

	class _MoneyInput(QDoubleSpinBox):
		def value_decimal(self):
			return Decimal(str(self.value())).quantize(Decimal("0.01"))
