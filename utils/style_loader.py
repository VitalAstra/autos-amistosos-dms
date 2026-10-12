"""Carga la hoja de estilos QSS del proyecto."""

from pathlib import Path

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

def load_stylesheet(app_or_window):
	"""Lee y aplica el estilo global desde ``assets/style.qss``."""
	stylesheet_path = Path(__file__).resolve().parent.parent / "assets" / "style.qss"
	try:
		stylesheet = stylesheet_path.read_text(encoding="utf-8")
	except OSError as error:
		raise OSError(
			f"No se pudo leer la hoja de estilos: {stylesheet_path}"
		) from error

	if isinstance(app_or_window, QApplication):
		app_or_window.setStyle("Fusion")
		palette = app_or_window.palette()
		role_colors = {
			QPalette.ColorRole.Window: "#F8F9FA",
			QPalette.ColorRole.WindowText: "#212529",
			QPalette.ColorRole.Base: "#FFFFFF",
			QPalette.ColorRole.AlternateBase: "#F8F9FA",
			QPalette.ColorRole.ToolTipBase: "#FFFFFF",
			QPalette.ColorRole.ToolTipText: "#212529",
			QPalette.ColorRole.Text: "#212529",
			QPalette.ColorRole.Button: "#E9ECEF",
			QPalette.ColorRole.ButtonText: "#212529",
			QPalette.ColorRole.BrightText: "#FFFFFF",
			QPalette.ColorRole.Highlight: "#DEE2E6",
			QPalette.ColorRole.HighlightedText: "#212529",
			QPalette.ColorRole.PlaceholderText: "#6C757D",
		}
		for group in (
			QPalette.ColorGroup.Active,
			QPalette.ColorGroup.Inactive,
			QPalette.ColorGroup.Disabled,
		):
			for role, color in role_colors.items():
				palette.setColor(group, role, QColor(color))
		app_or_window.setPalette(palette)
	app_or_window.setStyleSheet(stylesheet)
