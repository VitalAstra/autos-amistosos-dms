from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
	QFrame,
	QHBoxLayout,
	QLabel,
	QPushButton,
	QTableWidget,
	QTableWidgetItem,
	QVBoxLayout,
	QWidget,
)


class VehicleView(QWidget):
	"""Vista tabular del inventario de vehículos."""

	new_vehicle_requested = Signal()

	_COLUMNS = (
		("id", "VIN"),
		("condition", "Condición"),
		("manufacturer", "Fabricante"),
		("model", "Modelo"),
		("list_price", "Precio"),
	)

	def __init__(self, parent=None):
		super().__init__(parent)
		card = QFrame()
		card.setObjectName("card")
		card_layout = QVBoxLayout(card)
		card_layout.setContentsMargins(16, 16, 16, 16)
		card_layout.setSpacing(12)
		title = QLabel("Inventario de vehículos")
		title.setObjectName("viewTitle")
		header_layout = QHBoxLayout()
		header_layout.addWidget(title)
		header_layout.addStretch(1)
		self.new_vehicle_button = QPushButton("Alta de vehículo")
		self.new_vehicle_button.setObjectName("primaryButton")
		self.new_vehicle_button.clicked.connect(self.new_vehicle_requested)
		header_layout.addWidget(self.new_vehicle_button)
		card_layout.addLayout(header_layout)

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

		layout = QVBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.addWidget(card)

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
