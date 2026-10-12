from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QMessageBox,
)


class NewEmployeeView(QWidget):
    """Formulario simple para crear un nuevo empleado.

    Emite save_requested con un diccionario con los campos recogidos.
    """

    save_requested = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo empleado")
        self.setWindowFlag(Qt.Window, True)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.first_name = QLineEdit()
        self.first_name.setPlaceholderText("Nombre")

        self.last_name = QLineEdit()
        self.last_name.setPlaceholderText("Apellido")

        self.role = QComboBox()
        self.role.addItems(["Vendedor", "Gerente", "Administración", "Servicio"])

        form.addRow("Nombre", self.first_name)
        form.addRow("Apellido", self.last_name)
        form.addRow("Rol", self.role)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        self.save_btn = QPushButton("Guardar empleado")
        self.cancel_btn = QPushButton("Cancelar")
        self.save_btn.clicked.connect(self._on_save)
        self.cancel_btn.clicked.connect(lambda: self.close())
        buttons.addStretch(1)
        buttons.addWidget(self.cancel_btn)
        buttons.addWidget(self.save_btn)
        layout.addLayout(buttons)

    def _on_save(self):
        first = self.first_name.text().strip()
        last = self.last_name.text().strip()
        if not first or not last:
            QMessageBox.warning(self, "Datos incompletos", "Nombre y apellido son obligatorios.")
            return
        data = {
            "first_name": first,
            "last_name": last,
            "role": self.role.currentText(),
        }
        self.save_requested.emit(data)

    def show_save_result(self, success, message):
        if success:
            QMessageBox.information(self, "Empleado creado", message)
            self.close()
        else:
            QMessageBox.critical(self, "Error al guardar empleado", message)
