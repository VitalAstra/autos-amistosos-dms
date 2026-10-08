"""Carga la hoja de estilos QSS del proyecto."""

from pathlib import Path


def load_stylesheet(app_or_window):
	"""Lee y aplica el estilo global desde ``assets/style.qss``."""
	stylesheet_path = Path(__file__).resolve().parent.parent / "assets" / "style.qss"
	try:
		stylesheet = stylesheet_path.read_text(encoding="utf-8")
	except OSError as error:
		raise OSError(
			f"No se pudo leer la hoja de estilos: {stylesheet_path}"
		) from error

	app_or_window.setStyleSheet(stylesheet)
