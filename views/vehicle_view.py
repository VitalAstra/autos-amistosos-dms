from PySide6.QtWidgets import (
	QFormLayout,
	QFrame,
	QLabel,
	QLineEdit,
	QPushButton,
	QScrollArea,
	QTableWidget,
	QTableWidgetItem,
	QVBoxLayout,
	QHBoxLayout,
	QWidget,
)
from PySide6.QtCore import Signal


class VehicleView(QWidget):
	"""Vista tabular del inventario de vehículos."""

	vehicle_save_requested = Signal(dict)

	_COLUMNS = (
		("id", "VIN"),
		("condition", "Condición"),
		("manufacturer", "Fabricante"),
		("model", "Modelo"),
		("manufacture_date", "Fecha fabricación"),
		("manufacture_location", "Origen fabricación"),
		("cylinder_count", "Cilindros"),
		("door_count", "Puertas"),
		("weight", "Peso"),
		("capacity", "Capacidad"),
		("color", "Color"),
		("factory_options", "Opciones"),
		("list_price", "Precio"),
		("delivery_date", "Fecha entrega"),
		("delivery_mileage", "Kilometraje entrega"),
	)
	_FORM_FIELDS = (
		("vehicle_id", "VIN"),
		("condition", "Condición"),
		("manufacturer", "Fabricante"),
		("model", "Modelo"),
		("manufacture_date", "Fecha fabricación (AAAA-MM-DD)"),
		("manufacture_location", "Lugar de fabricación"),
		("cylinder_count", "Cilindros"),
		("door_count", "Puertas"),
		("weight", "Peso"),
		("capacity", "Capacidad"),
		("color", "Color"),
		("factory_options", "Opciones de fábrica"),
		("list_price", "Precio de lista (USD)"),
		("delivery_date", "Fecha de entrega (AAAA-MM-DD)"),
		("delivery_mileage", "Kilometraje de entrega"),
	)

	def __init__(self, parent=None):
		super().__init__(parent)
		main_layout = QHBoxLayout(self)
		main_layout.setContentsMargins(0, 0, 0, 0)
		main_layout.setSpacing(12)

		form_card = QFrame()
		form_card.setObjectName("card")
		form_layout = QVBoxLayout(form_card)
		form_layout.setContentsMargins(16, 16, 16, 16)
		title = QLabel("Alta de vehículo")
		title.setObjectName("viewTitle")
		form_layout.addWidget(title)

		form_container = QWidget()
		form = QFormLayout(form_container)
		form.setVerticalSpacing(8)
		self.inputs = {}
		for field, label in self._FORM_FIELDS:
			input_field = QLineEdit()
			self.inputs[field] = input_field
			form.addRow(label, input_field)

		form_scroll = QScrollArea()
		form_scroll.setWidgetResizable(True)
		form_scroll.setWidget(form_container)
		form_layout.addWidget(form_scroll, 1)
		self.save_button = QPushButton("Guardar vehículo")
		self.save_button.setObjectName("primaryButton")
		self.save_button.clicked.connect(self._emit_save_requested)
		form_layout.addWidget(self.save_button)

		card = QFrame()
		card.setObjectName("card")
		card_layout = QVBoxLayout(card)
		card_layout.setContentsMargins(16, 16, 16, 16)
		card_layout.setSpacing(12)
		title = QLabel("Inventario de vehículos")
		title.setObjectName("viewTitle")
		card_layout.addWidget(title)

		self.vehicles_table = QTableWidget(0, len(self._COLUMNS))
		self.vehicles_table.setHorizontalHeaderLabels(
			[label for _, label in self._COLUMNS]
		)
		self.vehicles_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
		self.vehicles_table.setSelectionBehavior(
			QTableWidget.SelectionBehavior.SelectRows
		)
		self.vehicles_table.setAlternatingRowColors(True)
		self.vehicles_table.verticalHeader().setVisible(False)
		self.vehicles_table.horizontalHeader().setStretchLastSection(True)

		card_layout.addWidget(self.vehicles_table)

		main_layout.addWidget(form_card, 1)
		main_layout.addWidget(card, 2)

	def get_form_data(self):
		return {
			field: input_field.text().strip()
			for field, input_field in self.inputs.items()
		}

	def clear_form(self):
		for input_field in self.inputs.values():
			input_field.clear()

	def _emit_save_requested(self):
		self.vehicle_save_requested.emit(self.get_form_data())

	def load_data(self, vehicles):
		"""Puebla la tabla con instancias ORM de vehículo."""
		self.vehicles_table.setRowCount(len(vehicles))
		self.vehicles_table.clearContents()
		for row_index, vehicle in enumerate(vehicles):
			for column_index, (field_name, _) in enumerate(self._COLUMNS):
				value = getattr(vehicle, field_name)
				text = "" if value is None else str(value)
				self.vehicles_table.setItem(
					row_index, column_index, QTableWidgetItem(text)
				)
