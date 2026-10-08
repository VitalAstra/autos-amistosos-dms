from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
	QFrame,
	QGraphicsDropShadowEffect,
	QHeaderView,
	QHBoxLayout,
	QLabel,
	QListWidget,
	QTableWidget,
	QTableWidgetItem,
	QVBoxLayout,
	QWidget,
)


class DashboardView(QWidget):
	"""Panel principal con métricas, ventas recientes y accesos rápidos."""

	quick_action_requested = Signal(str)

	_METRICS = (
		("vehicles_available", "Vehículos Disponibles", "42"),
		("monthly_sales", "Ventas del Mes", "18"),
		("new_prospects", "Prospectos Nuevos", "105"),
		("invoiced_revenue", "Ingresos Facturados", "$450,200.00"),
	)
	_SALES_COLUMNS = ("Factura", "Cliente", "Vehículo", "Monto", "Fecha")
	_SALES_KEYS = {
		"Factura": ("Factura", "invoice_number"),
		"Cliente": ("Cliente", "customer_name"),
		"Vehículo": ("Vehículo", "vehicle"),
		"Monto": ("Monto", "amount"),
		"Fecha": ("Fecha", "date"),
	}
	_QUICK_ACTIONS = (
		"Registrar Cliente",
		"Alta de Vehículo",
		"Nueva Venta",
	)

	def __init__(self, parent=None):
		super().__init__(parent)

		main_layout = QVBoxLayout(self)
		main_layout.setContentsMargins(0, 0, 0, 0)
		main_layout.setSpacing(16)

		metrics_row = QHBoxLayout()
		metrics_row.setSpacing(12)
		self.metric_values = {}
		for key, title, initial_value in self._METRICS:
			card, value_label = self._create_metric_card(title, initial_value)
			self.metric_values[key] = value_label
			metrics_row.addWidget(card)
		main_layout.addLayout(metrics_row)

		content_row = QHBoxLayout()
		content_row.setSpacing(12)

		sales_card = self._create_card()
		sales_layout = QVBoxLayout(sales_card)
		sales_layout.setContentsMargins(16, 16, 16, 16)
		sales_layout.setSpacing(12)
		sales_title = QLabel("Últimas ventas")
		sales_title.setObjectName("viewTitle")
		sales_layout.addWidget(sales_title)

		self.sales_table = QTableWidget(0, len(self._SALES_COLUMNS))
		self.sales_table.setHorizontalHeaderLabels(list(self._SALES_COLUMNS))
		self.sales_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
		self.sales_table.setSelectionBehavior(
			QTableWidget.SelectionBehavior.SelectRows
		)
		self.sales_table.setSelectionMode(
			QTableWidget.SelectionMode.SingleSelection
		)
		self.sales_table.setAlternatingRowColors(True)
		self.sales_table.verticalHeader().setVisible(False)
		self.sales_table.horizontalHeader().setSectionResizeMode(
			QHeaderView.ResizeMode.Stretch
		)
		sales_layout.addWidget(self.sales_table)
		content_row.addWidget(sales_card, 3)

		actions_card = self._create_card()
		actions_layout = QVBoxLayout(actions_card)
		actions_layout.setContentsMargins(16, 16, 16, 16)
		actions_layout.setSpacing(12)
		actions_title = QLabel("Accesos rápidos")
		actions_title.setObjectName("viewTitle")
		actions_layout.addWidget(actions_title)

		self.quick_actions = QListWidget()
		self.quick_actions.addItems(list(self._QUICK_ACTIONS))
		self.quick_actions.itemClicked.connect(self._on_quick_action_clicked)
		actions_layout.addWidget(self.quick_actions)
		content_row.addWidget(actions_card, 1)

		main_layout.addLayout(content_row, 1)

	def update_metrics(self, data_dict):
		"""Actualiza las tarjetas con los valores presentes en ``data_dict``.

		Las claves admitidas son ``vehicles_available``, ``monthly_sales``,
		``new_prospects`` e ``invoiced_revenue``. Las claves omitidas
		conservan su valor actual.
		"""
		for key, value in data_dict.items():
			if key in self.metric_values:
				self.metric_values[key].setText(str(value))

	def load_recent_sales(self, sales):
		"""Carga hasta cinco ventas, ordenadas de la más reciente a la anterior."""
		recent_sales = list(sales)[:5]
		self.sales_table.setRowCount(len(recent_sales))
		self.sales_table.clearContents()

		for row_index, sale in enumerate(recent_sales):
			for column_index, column in enumerate(self._SALES_COLUMNS):
				value = self._get_sale_value(sale, column)
				text = "" if value is None else str(value)
				self.sales_table.setItem(
					row_index, column_index, QTableWidgetItem(text)
				)

	@staticmethod
	def _create_card():
		card = QFrame()
		card.setObjectName("card")
		shadow = QGraphicsDropShadowEffect(card)
		shadow.setBlurRadius(16)
		shadow.setOffset(0, 3)
		shadow.setColor(QColor(33, 37, 41, 24))
		card.setGraphicsEffect(shadow)
		return card

	@classmethod
	def _create_metric_card(cls, title, initial_value):
		card = cls._create_card()
		layout = QVBoxLayout(card)
		layout.setContentsMargins(16, 16, 16, 16)
		layout.setSpacing(8)

		title_label = QLabel(title)
		title_label.setObjectName("metricTitle")
		value_label = QLabel(initial_value)
		value_label.setObjectName("metricValue")
		value_label.setWordWrap(True)
		layout.addWidget(title_label)
		layout.addWidget(value_label)
		layout.addStretch(1)
		return card, value_label

	def _on_quick_action_clicked(self, item):
		self.quick_action_requested.emit(item.text())

	@classmethod
	def _get_sale_value(cls, sale, column):
		keys = cls._SALES_KEYS[column]
		if isinstance(sale, dict):
			for key in keys:
				if key in sale:
					return sale[key]
			return None
		for key in keys:
			if hasattr(sale, key):
				return getattr(sale, key)
		return None
