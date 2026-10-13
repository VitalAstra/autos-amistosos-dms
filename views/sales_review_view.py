from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
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


class SalesReviewView(QWidget):
	approve_requested = Signal(int)
	reject_requested = Signal(int, str)
	cancel_requested = Signal(int, str)

	_COLUMNS = (
		"Factura",
		"Estado",
		"Fecha",
		"Cliente",
		"Vehículo",
		"Vendedor",
		"Total USD",
	)

	def __init__(self, parent=None):
		super().__init__(parent)
		card = QFrame()
		card.setObjectName("card")
		layout = QVBoxLayout(card)
		layout.setContentsMargins(16, 16, 16, 16)
		layout.setSpacing(12)
		title = QLabel("Ventas pendientes y aprobadas")
		title.setObjectName("viewTitle")
		layout.addWidget(title)

		self.sales_table = QTableWidget(0, len(self._COLUMNS))
		self.sales_table.setHorizontalHeaderLabels(list(self._COLUMNS))
		self.sales_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
		self.sales_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
		self.sales_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
		self.sales_table.currentCellChanged.connect(self._update_actions)
		self.sales_table.setAlternatingRowColors(True)
		self.sales_table.verticalHeader().setVisible(False)
		self.sales_table.horizontalHeader().setStretchLastSection(True)
		layout.addWidget(self.sales_table, 1)

		actions = QHBoxLayout()
		self.reason_input = QLineEdit()
		self.reason_input.setPlaceholderText("Motivo requerido para rechazar o cancelar")
		self.approve_button = QPushButton("Aprobar")
		self.reject_button = QPushButton("Rechazar")
		self.cancel_button = QPushButton("Cancelar venta")
		self.approve_button.clicked.connect(self._approve_selected)
		self.reject_button.clicked.connect(self._reject_selected)
		self.cancel_button.clicked.connect(self._cancel_selected)
		self._update_actions()
		actions.addWidget(self.reason_input, 1)
		actions.addWidget(self.approve_button)
		actions.addWidget(self.reject_button)
		actions.addWidget(self.cancel_button)
		layout.addLayout(actions)

		root_layout = QVBoxLayout(self)
		root_layout.setContentsMargins(0, 0, 0, 0)
		root_layout.addWidget(card)

	def load_data(self, invoices):
		self.sales_table.setRowCount(len(invoices))
		self.sales_table.clearContents()
		for row, invoice in enumerate(invoices):
			vehicle = invoice.vehicle
			customer = invoice.customer
			employee = invoice.employee
			values = (
				invoice.id,
				invoice.status,
				invoice.date,
				f"{customer.first_name} {customer.last_name}",
				f"{vehicle.manufacturer} {vehicle.model} ({vehicle.id})",
				f"{employee.first_name} {employee.last_name}",
				f"${invoice.total_amount:,.2f}",
			)
			for column, value in enumerate(values):
				self.sales_table.setItem(
					row, column, QTableWidgetItem(str(value))
				)
		self._update_actions()

	def _selected_invoice_id(self):
		row = self.sales_table.currentRow()
		item = self.sales_table.item(row, 0) if row >= 0 else None
		return int(item.text()) if item else None

	def _approve_selected(self):
		invoice_id = self._selected_invoice_id()
		if invoice_id is not None:
			self.approve_requested.emit(invoice_id)

	def _reject_selected(self):
		invoice_id = self._selected_invoice_id()
		if invoice_id is not None:
			self.reject_requested.emit(invoice_id, self.reason_input.text().strip())

	def _cancel_selected(self):
		invoice_id = self._selected_invoice_id()
		if invoice_id is not None:
			self.cancel_requested.emit(invoice_id, self.reason_input.text().strip())

	def _update_actions(self, *_):
		row = self.sales_table.currentRow()
		status_item = self.sales_table.item(row, 1) if row >= 0 else None
		status = status_item.text() if status_item else ""
		self.approve_button.setEnabled(status == "pending")
		self.reject_button.setEnabled(status == "pending")
		self.cancel_button.setEnabled(status in {"pending", "approved"})