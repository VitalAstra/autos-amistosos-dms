import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from config.database import init_db
from utils.style_loader import load_stylesheet
from views.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    load_stylesheet(app)
    try:
        init_db()
    except Exception as error:
        QMessageBox.critical(None, "Esquema de base de datos", str(error))
        return 1

    # Acceso directo temporal: no se atribuyen acciones a un empleado ficticio.
    window = MainWindow(None)
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())