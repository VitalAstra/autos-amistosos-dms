from PySide6.QtWidgets import (
	QFrame,
	QLabel,
	QTableWidget,
	QTableWidgetItem,
	QVBoxLayout,
	QWidget,
)


class VehicleView(QWidget):
	"""Vista tabular del inventario de vehículos."""

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
