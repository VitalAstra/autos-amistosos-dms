import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from config.database import DatabaseConnection
from views.main_window import MainWindow

def main():
    app = QApplication(sys.argv)

    # Validar conexión a PostgreSQL antes de iniciar la interfaz
    try:
        conn = DatabaseConnection.get_connection()
        conn.close()
        print("Conexión a PostgreSQL establecida correctamente.")
    except Exception as e:
        QMessageBox.critical(
            None, 
            "Error de Conexión", 
            f"No se pudo conectar a la base de datos PostgreSQL.\n\nVerifica tu archivo .env\nDetalle: {e}"
        )
        sys.exit(1)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()