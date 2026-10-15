"""Prototipo visual de cómo llegarían las encuestas desde distintos canales."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
	QFrame,
	QHBoxLayout,
	QLabel,
	QListWidget,
	QListWidgetItem,
	QVBoxLayout,
	QWidget,
)


class SurveyView(QWidget):
	"""Bandeja demostrativa de encuestas recibidas desde canales externos."""

	def __init__(self, messages: list[dict[str, object]], parent=None):
		super().__init__(parent)
		self._messages = list(messages)

		main_layout = QVBoxLayout(self)
		main_layout.setContentsMargins(0, 0, 0, 0)
		main_layout.setSpacing(12)

		title = QLabel("Encuestas")
		title.setObjectName("viewTitle")
		main_layout.addWidget(title)

		prototype_notice = QLabel(
			"PROTOTIPO · Ejemplos visuales; no recibe mensajes reales "
			"ni guarda respuestas."
		)
		prototype_notice.setWordWrap(True)
		prototype_notice.setObjectName("sectionTitle")
		main_layout.addWidget(prototype_notice)

		content_layout = QHBoxLayout()
		content_layout.setSpacing(12)

		inbox_card = QFrame()
		inbox_card.setObjectName("card")
		inbox_layout = QVBoxLayout(inbox_card)
		inbox_layout.setContentsMargins(14, 14, 14, 14)
		inbox_layout.setSpacing(8)
		inbox_title = QLabel("Ejemplos de recepción")
		inbox_title.setObjectName("sectionTitle")
		inbox_layout.addWidget(inbox_title)

		self.inbox_list = QListWidget()
		self.inbox_list.setSpacing(4)
		for message in self._messages:
			item = QListWidgetItem(
				f"{message['channel']}  ·  {message['sender']}\n"
				f"{message['subject']}\n"
				f"{message['received_at']}"
			)
			item.setData(Qt.ItemDataRole.UserRole, message["id"])
			self.inbox_list.addItem(item)
		self.inbox_list.currentRowChanged.connect(self._show_message)
		inbox_layout.addWidget(self.inbox_list, 1)
		content_layout.addWidget(inbox_card, 2)

		preview_card = QFrame()
		preview_card.setObjectName("card")
		preview_layout = QVBoxLayout(preview_card)
		preview_layout.setContentsMargins(20, 20, 20, 20)
		preview_layout.setSpacing(14)

		self.channel_label = QLabel("Selecciona un ejemplo")
		self.channel_label.setObjectName("viewTitle")
		preview_layout.addWidget(self.channel_label)

		self.sender_label = QLabel()
		self.sender_label.setWordWrap(True)
		preview_layout.addWidget(self.sender_label)

		self.subject_label = QLabel()
		self.subject_label.setObjectName("sectionTitle")
		self.subject_label.setWordWrap(True)
		preview_layout.addWidget(self.subject_label)

		self.message_frame = QFrame()
		self.message_frame.setObjectName("subCard")
		message_layout = QVBoxLayout(self.message_frame)
		message_layout.setContentsMargins(16, 14, 16, 14)
		message_caption = QLabel("MENSAJE RECIBIDO")
		message_caption.setObjectName("metricTitle")
		self.message_label = QLabel()
		self.message_label.setWordWrap(True)
		message_layout.addWidget(message_caption)
		message_layout.addWidget(self.message_label)
		preview_layout.addWidget(self.message_frame)

		ratings_frame = QFrame()
		ratings_frame.setObjectName("subCard")
		ratings_layout = QVBoxLayout(ratings_frame)
		ratings_layout.setContentsMargins(16, 14, 16, 14)
		ratings_layout.setSpacing(8)
		ratings_title = QLabel("RESPUESTA DE ENCUESTA")
		ratings_title.setObjectName("metricTitle")
		ratings_layout.addWidget(ratings_title)
		self.rating_labels = {}
		for category in ("Vehículo", "Concesionario", "Vendedor"):
			rating = QLabel()
			rating.setWordWrap(True)
			self.rating_labels[category] = rating
			ratings_layout.addWidget(rating)
		preview_layout.addWidget(ratings_frame)

		self.reference_label = QLabel()
		self.reference_label.setObjectName("metricTitle")
		self.reference_label.setWordWrap(True)
		preview_layout.addWidget(self.reference_label)
		preview_layout.addStretch(1)
		content_layout.addWidget(preview_card, 3)
		main_layout.addLayout(content_layout, 1)

		if self._messages:
			self.inbox_list.setCurrentRow(0)

	def _show_message(self, row: int):
		if row < 0 or row >= len(self._messages):
			return
		message = self._messages[row]
		self.channel_label.setText(str(message["channel"]))
		self.sender_label.setText(
			f"De: {message['sender']}  ·  {message['address']}\n"
			f"Recibido: {message['received_at']}"
		)
		self.subject_label.setText(str(message["subject"]))
		self.message_label.setText(str(message["message"]))
		ratings = message["ratings"]
		for category, label in self.rating_labels.items():
			rating = ratings.get(category)
			label.setText(
				f"{category}: {'★' * int(rating)}{'☆' * (5 - int(rating))} "
				f"({rating}/5)"
			)
		self.reference_label.setText(
			f"Referencia de ejemplo: {message['reference']}"
		)
