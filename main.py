import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from config.database import init_db
from utils.style_loader import load_stylesheet
from views.login_dialog import LoginDialog
from views.main_window import MainWindow


def main():
    QApplication.setAttribute(
        Qt.ApplicationAttribute.AA_DontUseNativeDialogs, True
    )
    app = QApplication(sys.argv)
    load_stylesheet(app)
    try:
        init_db()
    except Exception as error:
        QMessageBox.critical(None, "Esquema de base de datos", str(error))
        return 1

    login = LoginDialog()
    if login.exec() != LoginDialog.DialogCode.Accepted:
        return 0
    window = MainWindow(login.employee)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
