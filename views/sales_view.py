from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class SalesView(QWidget):
	"""Vista tabular del resumen de ventas."""

	_COLUMNS = (
		("Número Factura", "Número Factura"),
		("Fecha", "Fecha"),
		("Nombre Cliente", "Nombre Cliente"),
		("Modelo Vehículo", "Modelo Vehículo"),
		("Monto Total", "Monto Total"),
	)

	def __init__(self, parent=None):
		super().__init__(parent)
		self.sales_table = QTableWidget(0, len(self._COLUMNS))
		self.sales_table.setHorizontalHeaderLabels(
			[label for _, label in self._COLUMNS]
		)
		self.sales_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
		self.sales_table.setSelectionBehavior(
			QTableWidget.SelectionBehavior.SelectRows
		)
		self.sales_table.setAlternatingRowColors(True)
		self.sales_table.horizontalHeader().setStretchLastSection(True)

		layout = QVBoxLayout(self)
		layout.addWidget(self.sales_table)

	def load_data(self, sales_list):
		"""Puebla la tabla con el resumen de ventas recibido."""
		self.sales_table.setRowCount(len(sales_list))
		self.sales_table.clearContents()
		for row_index, sale in enumerate(sales_list):
			for column_index, (field_name, _) in enumerate(self._COLUMNS):
				value = sale.get(field_name) if isinstance(sale, dict) else None
				text = "" if value is None else str(value)
				self.sales_table.setItem(
					row_index, column_index, QTableWidgetItem(text)
				)
