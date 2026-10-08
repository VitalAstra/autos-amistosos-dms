"""Validadores reutilizables para campos de entrada PySide6."""

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import QLineEdit


def set_vin_validator(line_edit: QLineEdit) -> None:
	"""Restringe el campo a un VIN de 17 caracteres en mayúsculas."""
	pattern = QRegularExpression(r"[A-HJ-NPR-Z0-9]{17}")
	line_edit.setValidator(QRegularExpressionValidator(pattern, line_edit))


def set_phone_validator(line_edit: QLineEdit) -> None:
	"""Restringe el campo telefónico a entre 8 y 15 dígitos ASCII."""
	pattern = QRegularExpression(r"[0-9]{8,15}")
	line_edit.setValidator(QRegularExpressionValidator(pattern, line_edit))


def set_currency_validator(line_edit: QLineEdit) -> None:
	"""Permite montos no negativos con hasta dos decimales."""
	pattern = QRegularExpression(r"[0-9]+(?:\.[0-9]{0,2})?")
	line_edit.setValidator(QRegularExpressionValidator(pattern, line_edit))