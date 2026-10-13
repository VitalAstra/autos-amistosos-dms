from PySide6.QtWidgets import (
	QFormLayout,
	QFrame,
	QHBoxLayout,
	QLabel,
	QTableWidget,
	QTableWidgetItem,
	QVBoxLayout,
	QWidget,
)


class SalesHistoryView(QWidget):
	"""Consulta del historial de facturas y detalle de la factura seleccionada."""

	_COLUMNS = (
		("invoice_number", "Factura"),
		("date", "Fecha"),
		("customer_name", "Cliente"),
		("vehicle_id", "VIN"),
		("total_amount", "Total"),
	)

	def __init__(self, parent=None):
		super().__init__(parent)
		main_layout = QVBoxLayout(self)
		main_layout.setContentsMargins(0, 0, 0, 0)
		main_layout.setSpacing(12)

		self.title = QLabel("Historial de ventas")
		self.title.setObjectName("viewTitle")
		main_layout.addWidget(self.title)

		content_layout = QHBoxLayout()
		content_layout.setSpacing(12)

		table_card = QFrame()
		table_card.setObjectName("card")
		table_layout = QVBoxLayout(table_card)
		table_layout.setContentsMargins(16, 16, 16, 16)
		self.sales_table = QTableWidget(0, len(self._COLUMNS))
		self.sales_table.setHorizontalHeaderLabels(
			[label for _, label in self._COLUMNS]
		)
		self.sales_table.setEditTriggers(
			QTableWidget.EditTrigger.NoEditTriggers
		)
		self.sales_table.setSelectionBehavior(
			QTableWidget.SelectionBehavior.SelectRows
		)
		self.sales_table.setSelectionMode(
			QTableWidget.SelectionMode.SingleSelection
		)
		self.sales_table.setAlternatingRowColors(True)
		self.sales_table.verticalHeader().setVisible(False)
		self.sales_table.horizontalHeader().setStretchLastSection(True)
		self.sales_table.cellClicked.connect(self._show_selected_sale)
		table_layout.addWidget(self.sales_table)
		content_layout.addWidget(table_card, 3)

		detail_card = QFrame()
		detail_card.setObjectName("card")
		detail_layout = QVBoxLayout(detail_card)
		detail_layout.setContentsMargins(16, 16, 16, 16)
		detail_title = QLabel("Detalle de factura")
		detail_title.setObjectName("viewTitle")
		detail_layout.addWidget(detail_title)
		self.detail_labels = {}
		detail_form = QFormLayout()
		for key, label in (
			("invoice_number", "Número de factura"),
			("date", "Fecha"),
			("customer_name", "Cliente"),
			("vehicle", "Vehículo"),
			("vehicle_id", "VIN"),
			("employee_name", "Vendedor"),
			("negotiated_price", "Precio negociado"),
			("tax_amount", "Impuestos"),
			("license_fee_amount", "Costo de placas"),
			("total_amount", "Total"),
		):
			value_label = QLabel("—")
			value_label.setWordWrap(True)
			self.detail_labels[key] = value_label
			detail_form.addRow(label, value_label)
		detail_layout.addLayout(detail_form)
		detail_layout.addStretch(1)
		content_layout.addWidget(detail_card, 2)
		main_layout.addLayout(content_layout, 1)

	def load_sales(self, sales):
		"""Carga facturas recuperadas por el controlador ORM."""
		self._sales = list(sales)
		self.sales_table.setRowCount(len(self._sales))
		self.sales_table.clearContents()
		self._clear_detail()
		for row, sale in enumerate(self._sales):
			for column, (key, _) in enumerate(self._COLUMNS):
				value = sale.get(key)
				if key == "total_amount" and value is not None:
					text = self._format_money(value)
				elif key == "date" and value is not None:
					text = value.isoformat()
				else:
					text = "—" if value is None else str(value)
				self.sales_table.setItem(
					row, column, QTableWidgetItem(text)
				)
		if not self._sales:
			self.title.setText(
				"Historial de ventas — No hay ventas registradas"
			)
		else:
			self.title.setText("Historial de ventas")

	def _show_selected_sale(self, row, _):
		if row < 0 or row >= len(self._sales):
			return
		sale = self._sales[row]
		for key, label in self.detail_labels.items():
			value = sale.get(key)
			if key.endswith("_amount") or key == "negotiated_price":
				text = self._format_money(value) if value is not None else "—"
			elif key == "date" and value is not None:
				text = value.isoformat()
			else:
				text = "—" if value is None else str(value)
			label.setText(text)

	def _clear_detail(self):
		for label in self.detail_labels.values():
			label.setText("—")

	@staticmethod
	def _format_money(amount):
		return f"${amount:,.2f}"
