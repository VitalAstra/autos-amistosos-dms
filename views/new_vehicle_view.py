from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QMessageBox,
)

from utils.validators import set_vin_validator


class NewVehicleView(QWidget):
    """Formulario sencillo para crear un nuevo vehículo.

    Emite save_requested con un diccionario con los campos recogidos.
    """

    save_requested = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo vehículo")
        self.setWindowFlag(Qt.Window, True)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.vin_input = QLineEdit()
        set_vin_validator(self.vin_input)
        self.vin_input.setPlaceholderText("VIN (17 caracteres)")

        self.condition_combo = QComboBox()
        self.condition_combo.addItems(["Nuevo", "Usado", "Certif."])

        self.manufacturer_input = QLineEdit()
        self.manufacturer_input.setPlaceholderText("Fabricante")

        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("Modelo")

        self.manufacture_date = QDateEdit()
        self.manufacture_date.setCalendarPopup(True)
        self.manufacture_date.setDate(QDate.currentDate())

        self.list_price = QDoubleSpinBox()
        self.list_price.setRange(0, 9_999_999_999)
        self.list_price.setDecimals(2)
        self.list_price.setPrefix("$ ")

        form.addRow("VIN", self.vin_input)
        form.addRow("Condición", self.condition_combo)
        form.addRow("Fabricante", self.manufacturer_input)
        form.addRow("Modelo", self.model_input)
        form.addRow("Fecha de fabricación", self.manufacture_date)
        form.addRow("Precio de lista", self.list_price)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        self.save_btn = QPushButton("Guardar vehículo")
        self.cancel_btn = QPushButton("Cancelar")
        self.save_btn.clicked.connect(self._on_save)
        self.cancel_btn.clicked.connect(lambda: self.close())
        buttons.addStretch(1)
        buttons.addWidget(self.cancel_btn)
        buttons.addWidget(self.save_btn)
        layout.addLayout(buttons)

    def _on_save(self):
        vin = self.vin_input.text().strip().upper()
        if len(vin) != 17:
            QMessageBox.warning(self, "VIN inválido", "El VIN debe tener 17 caracteres.")
            return
        manufacturer = self.manufacturer_input.text().strip()
        model = self.model_input.text().strip()
        if not manufacturer or not model:
            QMessageBox.warning(
                self,
                "Datos incompletos",
                "Fabricante y modelo son obligatorios.",
            )
            return
        if self.list_price.value() <= 0:
            QMessageBox.warning(
                self,
                "Precio inválido",
                "El precio de lista debe ser mayor que cero.",
            )
            return
        data = {
            "id": vin,
            "condition": self.condition_combo.currentText(),
            "manufacturer": manufacturer,
            "model": model,
            "manufacture_date": self.manufacture_date.date().toPython(),
            "list_price": float(self.list_price.value()),
        }
        self.save_requested.emit(data)

    def show_save_result(self, success, message):
        if success:
            QMessageBox.information(self, "Vehículo creado", message)
            self.close()
        else:
            QMessageBox.critical(self, "Error al guardar vehículo", message)
