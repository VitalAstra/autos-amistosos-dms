from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
	QComboBox,
	QFormLayout,
	QFrame,
	QHBoxLayout,
	QLabel,
	QLineEdit,
	QPushButton,
	QTableWidget,
	QTableWidgetItem,
	QVBoxLayout,
	QWidget,
)


class CustomerView(QWidget):
	"""Interfaz para registrar, buscar y consultar clientes."""

	save_requested = Signal(dict)
	search_changed = Signal(str)

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
		self.lead_source_input.addItem("Seleccionar origen", "")
		self.lead_source_input.addItems(
			[
				"Sitio web",
				"Redes sociales",
				"Referido",
				"Llamada telefónica",
				"Visita al concesionario",
				"Otro",
			]
		)

		form_layout.addRow("Nombre", self.first_name_input)
		form_layout.addRow("Apellidos", self.last_name_input)
		form_layout.addRow("Email", self.email_input)
		form_layout.addRow("Teléfono", self.phone_input)
		form_layout.addRow("Dirección", self.address_input)
		form_layout.addRow("Lead Source", self.lead_source_input)

		self.save_button = QPushButton("Guardar")
		self.clear_button = QPushButton("Limpiar")
		self.save_button.clicked.connect(self._emit_save_requested)
		self.clear_button.clicked.connect(self.clear_form)
		form_layout.addRow(self.save_button, self.clear_button)

		left_layout.addLayout(form_layout)

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

		right_layout.addLayout(search_layout)
		right_layout.addWidget(self.customers_table)

		main_layout.addWidget(left_section, 1)
		main_layout.addWidget(right_section, 2)

	def load_data(self, customers):
		"""Puebla la tabla con instancias ORM de cliente."""
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

	def get_form_data(self):
		"""Retorna los datos ingresados en el formulario."""
		return {
			"first_name": self.first_name_input.text().strip(),
			"last_name": self.last_name_input.text().strip(),
			"email": self.email_input.text().strip(),
			"phone": self.phone_input.text().strip(),
			"address": self.address_input.text().strip(),
			"lead_source": self.lead_source_input.currentText()
			if self.lead_source_input.currentData() != ""
			else "",
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

	def _emit_save_requested(self):
		self.save_requested.emit(self.get_form_data())

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
