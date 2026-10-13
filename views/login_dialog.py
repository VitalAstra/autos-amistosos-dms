from PySide6.QtWidgets import (
	QDialog,
	QFormLayout,
	QLabel,
	QLineEdit,
	QPushButton,
	QVBoxLayout,
)

from controllers.auth_controller import AuthController


class LoginDialog(QDialog):
	"""Solicita credenciales antes de abrir las funciones del DMS."""

	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("Autos Amistosos")
		self.setModal(True)
		self.employee = None
		self._auth_controller = AuthController()

		layout = QVBoxLayout(self)
		brand_label = QLabel("Autos Amistosos")
		brand_label.setObjectName("brandTitle")
		layout.addWidget(brand_label)
		layout.addWidget(QLabel("Inicia sesión con tu cuenta de empleado."))
		form = QFormLayout()
		self.username_input = QLineEdit()
		self.password_input = QLineEdit()
		self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
		form.addRow("Usuario", self.username_input)
		form.addRow("Contraseña", self.password_input)
		layout.addLayout(form)

		self.error_label = QLabel()
		self.error_label.setWordWrap(True)
		self.error_label.setStyleSheet("color: #B42318")
		layout.addWidget(self.error_label)

		login_button = QPushButton("Iniciar sesión")
		login_button.setObjectName("primaryButton")
		login_button.clicked.connect(self._authenticate)
		self.password_input.returnPressed.connect(self._authenticate)
		layout.addWidget(login_button)

	def _authenticate(self):
		employee = self._auth_controller.authenticate(
			self.username_input.text(), self.password_input.text()
		)
		if employee is None:
			self.password_input.clear()
			self.error_label.setText("Usuario o contraseña incorrectos, o cuenta inactiva.")
			return
		self.employee = employee
		self.accept()