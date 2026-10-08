from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class VehicleView(QWidget):
	"""Vista tabular del inventario de vehículos."""

	_COLUMNS = (
		("vehicle_id", "VIN"),
		("condition", "Condición"),
		("manufacturer", "Fabricante"),
		("model", "Modelo"),
		("color", "Color"),
		("list_price", "Precio"),
	)

	def __init__(self, parent=None):
		super().__init__(parent)
		self.vehicles_table = QTableWidget(0, len(self._COLUMNS))
		self.vehicles_table.setHorizontalHeaderLabels(
			[label for _, label in self._COLUMNS]
		)
		self.vehicles_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
		self.vehicles_table.setSelectionBehavior(
			QTableWidget.SelectionBehavior.SelectRows
		)
		self.vehicles_table.setAlternatingRowColors(True)
		self.vehicles_table.horizontalHeader().setStretchLastSection(True)

		layout = QVBoxLayout(self)
		layout.addWidget(self.vehicles_table)

	def load_data(self, vehicles_list):
		"""Puebla la tabla con los vehículos recibidos."""
		self.vehicles_table.setRowCount(len(vehicles_list))
		self.vehicles_table.clearContents()
		for row_index, vehicle in enumerate(vehicles_list):
			for column_index, (field_name, _) in enumerate(self._COLUMNS):
				value = (
					vehicle.get(field_name)
					if isinstance(vehicle, dict)
					else getattr(vehicle, field_name, None)
				)
				text = "" if value is None else str(value)
				self.vehicles_table.setItem(
					row_index, column_index, QTableWidgetItem(text)
				)
