import sys
from PySide6.QtWidgets import QApplication
from config.database import init_db
from utils.style_loader import load_stylesheet
from views.main_window import MainWindow


def main():
    init_db()
    app = QApplication(sys.argv)
    load_stylesheet(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()