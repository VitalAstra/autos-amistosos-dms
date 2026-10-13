from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
	QComboBox,
	QFormLayout,
	QFrame,
	QHBoxLayout,
	QLabel,
	QLineEdit,
	QMessageBox,
	QPushButton,
	QTableWidget,
	QTableWidgetItem,
	QVBoxLayout,
	QWidget,
)


class CustomerView(QWidget):
	"""Interfaz para registrar, buscar y consultar clientes."""

	save_requested = Signal(dict)
	update_requested = Signal(dict)
	delete_requested = Signal(int)
	search_changed = Signal(str)
	new_employee_requested = Signal()

	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("Clientes")

		main_layout = QHBoxLayout(self)
		main_layout.setContentsMargins(0, 0, 0, 0)
		main_layout.setSpacing(12)

		left_section = QFrame()
		left_section.setObjectName("card")
		left_layout = QVBoxLayout(left_section)
		left_layout.setContentsMargins(16, 16, 16, 16)
		left_layout.setSpacing(12)
		form_title = QLabel("Datos del cliente")
		form_title.setObjectName("viewTitle")
		left_layout.addWidget(form_title)

		form_layout = QFormLayout()
		form_layout.setVerticalSpacing(10)
		form_layout.setHorizontalSpacing(12)
		self.first_name_input = QLineEdit()
		self.last_name_input = QLineEdit()
		self.email_input = QLineEdit()
		self.phone_input = QLineEdit()
		self.address_input = QLineEdit()
		self.lead_source_input = QComboBox()
		self.lead_source_input.setEditable(True)
		self.lead_source_input.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
		self.lead_source_input.addItem("Seleccionar origen", "")
		self.lead_source_input.lineEdit().setPlaceholderText(
			"Selecciona o escribe un origen"
		)

		form_layout.addRow("Nombre", self.first_name_input)
		form_layout.addRow("Apellidos", self.last_name_input)
		form_layout.addRow("Email", self.email_input)
		form_layout.addRow("Teléfono", self.phone_input)
		form_layout.addRow("Dirección", self.address_input)
		form_layout.addRow("Lead Source", self.lead_source_input)

		# Botones: Guardar / Limpiar / Actualizar / Eliminar
		self.save_button = QPushButton("Guardar")
		self.update_button = QPushButton("Actualizar")
		self.delete_button = QPushButton("Eliminar")
		self.clear_button = QPushButton("Limpiar")
		self.save_button.clicked.connect(self._emit_save_requested)
		self.update_button.clicked.connect(self._emit_update_requested)
		self.delete_button.clicked.connect(self._emit_delete_requested)
		self.clear_button.clicked.connect(self.clear_form)
		buttons_container = QWidget()
		buttons_layout = QHBoxLayout(buttons_container)
		buttons_layout.setContentsMargins(0, 0, 0, 0)
		buttons_layout.setSpacing(8)
		buttons_layout.addWidget(self.save_button)
		buttons_layout.addWidget(self.update_button)
		buttons_layout.addWidget(self.delete_button)
		buttons_layout.addWidget(self.clear_button)
		form_layout.addRow(buttons_container)

		left_layout.addLayout(form_layout)

		employee_section = QFrame()
		employee_section.setObjectName("subCard")
		employee_layout = QVBoxLayout(employee_section)
		employee_layout.setContentsMargins(12, 12, 12, 12)
		employee_layout.setSpacing(8)
		employee_title = QLabel("Gestión de empleados")
		employee_title.setObjectName("sectionTitle")
		employee_layout.addWidget(employee_title)
		employee_layout.addWidget(
			QLabel("Registra el personal que podrá asignarse a las ventas.")
		)
		self.new_employee_button = QPushButton("Registrar nuevo empleado")
		self.new_employee_button.clicked.connect(
			self.new_employee_requested
		)
		employee_layout.addWidget(self.new_employee_button)
		left_layout.addWidget(employee_section)

		right_section = QFrame()
		right_section.setObjectName("card")
		right_layout = QVBoxLayout(right_section)
		right_layout.setContentsMargins(16, 16, 16, 16)
		right_layout.setSpacing(12)
		list_title = QLabel("Clientes registrados")
		list_title.setObjectName("viewTitle")
		right_layout.addWidget(list_title)

		search_layout = QHBoxLayout()
		search_layout.setSpacing(8)
		search_layout.addWidget(QLabel("Buscar"))
		self.search_input = QLineEdit()
		self.search_input.setPlaceholderText("Buscar clientes por nombre")
		self.search_input.textChanged.connect(self._on_search_changed)
		search_layout.addWidget(self.search_input)

		self.customers_table = QTableWidget(0, 5)
		self.customers_table.setHorizontalHeaderLabels(
			["ID", "Nombre Completo", "Email", "Teléfono", "Origen"]
		)
		self.customers_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
		self.customers_table.setSelectionBehavior(
			QTableWidget.SelectionBehavior.SelectRows
		)
		self.customers_table.setSelectionMode(
			QTableWidget.SelectionMode.SingleSelection
		)
		self.customers_table.setAlternatingRowColors(True)
		self.customers_table.verticalHeader().setVisible(False)
		self.customers_table.horizontalHeader().setStretchLastSection(True)
		# Conectar selección de fila para editar/eliminar
		self.customers_table.cellClicked.connect(self._on_table_cell_clicked)

		right_layout.addLayout(search_layout)
		right_layout.addWidget(self.customers_table)

		main_layout.addWidget(left_section, 1)
		main_layout.addWidget(right_section, 2)

	def load_data(self, customers):
		"""Puebla la tabla con instancias ORM de cliente."""
		# Mantener una referencia para seleccionar/editar más tarde
		self._customers = list(customers)
		self._selected_customer_id = None
		self.update_button.setEnabled(False)
		self.delete_button.setEnabled(False)

		self.customers_table.setRowCount(len(customers))
		self.customers_table.clearContents()

		for row_index, customer in enumerate(customers):
			first_name = customer.first_name
			last_name = customer.last_name
			full_name = f"{first_name} {last_name}".strip()
			values = (
				customer.id,
				full_name,
				customer.email,
				customer.phone,
				customer.lead_source,
			)
			for column_index, value in enumerate(values):
				text = "" if value is None else str(value)
				self.customers_table.setItem(
					row_index, column_index, QTableWidgetItem(text)
				)

		self._filter_rows(self.search_input.text())

	def load_lead_sources(self, lead_sources):
		current_text = self.lead_source_input.currentText()
		self.lead_source_input.clear()
		self.lead_source_input.addItem("Seleccionar origen", "")
		self.lead_source_input.addItems(lead_sources)
		self.lead_source_input.setCurrentText(current_text)

	def get_form_data(self):
		"""Retorna los datos ingresados en el formulario."""
		return {
			"first_name": self.first_name_input.text().strip(),
			"last_name": self.last_name_input.text().strip(),
			"email": self.email_input.text().strip(),
			"phone": self.phone_input.text().strip(),
			"address": self.address_input.text().strip(),
			"lead_source": (
				self.lead_source_input.currentText().strip()
				if self.lead_source_input.currentIndex() != 0
				else ""
			),
		}

	def clear_form(self):
		"""Limpia los campos del formulario."""
		for field in (
			self.first_name_input,
			self.last_name_input,
			self.email_input,
			self.phone_input,
			self.address_input,
		):
			field.clear()
		self.lead_source_input.setCurrentIndex(0)

	def show_save_result(self, success, message):
		"""Informa el resultado del registro del cliente."""
		if success:
			QMessageBox.information(self, "Cliente registrado", message)
			self.clear_form()
			return
		QMessageBox.warning(self, "No se pudo registrar el cliente", message)

	def _emit_save_requested(self):
		self.save_requested.emit(self.get_form_data())

	def _emit_update_requested(self):
		if self._selected_customer_id is None:
			return
		payload = dict(self.get_form_data())
		payload["id"] = self._selected_customer_id
		self.update_requested.emit(payload)

	def _emit_delete_requested(self):
		if self._selected_customer_id is None:
			return
		self.delete_requested.emit(self._selected_customer_id)

	def _on_table_cell_clicked(self, row, column):
		"""Selecciona la fila y carga los datos en el formulario para editar."""
		try:
			customer = self._customers[row]
		except Exception:
			return
		self._selected_customer_id = customer.id
		self.update_button.setEnabled(True)
		self.delete_button.setEnabled(True)
		# Poblar formulario
		self.first_name_input.setText(customer.first_name or "")
		self.last_name_input.setText(customer.last_name or "")
		self.email_input.setText(customer.email or "")
		self.phone_input.setText(customer.phone or "")
		self.address_input.setText(customer.address or "")
		# Seleccionar lead source si existe
		index = 0
		for i in range(self.lead_source_input.count()):
			if self.lead_source_input.itemText(i) == (customer.lead_source or ""):
				index = i
				break
		self.lead_source_input.setCurrentIndex(index)

	def _filter_rows(self, text):
		query = text.strip().casefold()
		for row_index in range(self.customers_table.rowCount()):
			name_item = self.customers_table.item(row_index, 1)
			full_name = name_item.text() if name_item else ""
			self.customers_table.setRowHidden(
				row_index, query not in full_name.casefold()
			)
		# Si el filter ocultó la fila seleccionada, cancelar selección
		if self._selected_customer_id is not None:
			visible = any(
				not self.customers_table.isRowHidden(r)
				and self.customers_table.item(r, 0).text() == str(self._selected_customer_id)
				for r in range(self.customers_table.rowCount())
			)
			if not visible:
				self._selected_customer_id = None
				self.update_button.setEnabled(False)
				self.delete_button.setEnabled(False)

	def _on_search_changed(self, text):
		self._filter_rows(text)
		self.search_changed.emit(text)

	def _filter_rows(self, text):
		query = text.strip().casefold()
		for row_index in range(self.customers_table.rowCount()):
			name_item = self.customers_table.item(row_index, 1)
			full_name = name_item.text() if name_item else ""
			self.customers_table.setRowHidden(
				row_index, query not in full_name.casefold()
			)
