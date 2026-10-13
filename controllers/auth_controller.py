"""Autenticación local de empleados con hashes PBKDF2."""

import base64
import hashlib
import hmac
import secrets

from sqlalchemy import func, select

from config.database import SessionLocal
from models.employee import Employee


class AuthController:
	_ITERATIONS = 310_000
	_SCHEME = "pbkdf2_sha256"

	def authenticate(self, username: str, password: str) -> Employee | None:
		if not isinstance(username, str) or not isinstance(password, str):
			return None
		with SessionLocal() as session:
			employee = session.scalars(
				select(Employee).where(
					Employee.username == username.strip(),
					Employee.is_active.is_(True),
				)
			).one_or_none()
			if employee is None or not self.verify_password(
				password, employee.password_hash
			):
				return None
			session.expunge(employee)
			return employee

	def set_credentials(
		self, employee_id: int, username: str, password: str
	) -> tuple[bool, str]:
		username, error = self._validate_credentials(username, password)
		if error:
			return False, error
		try:
			with SessionLocal() as session:
				employee = session.get(Employee, employee_id)
				if employee is None:
					return False, "No se encontró el empleado."
				employee.username = username
				employee.password_hash = self.hash_password(password)
				employee.is_active = True
				session.commit()
			return True, f"Credenciales configuradas para el empleado {employee_id}."
		except Exception as error:
			return False, f"No se pudieron guardar las credenciales: {error}"

	def list_employees_for_provisioning(self):
		with SessionLocal() as session:
			return session.execute(
				select(
					Employee.employee_id,
					Employee.first_name,
					Employee.last_name,
					Employee.role,
					Employee.username,
					Employee.is_active,
				).order_by(Employee.employee_id)
			).all()

	def bootstrap_initial_admin(
		self,
		first_name: str,
		last_name: str,
		username: str,
		password: str,
	) -> tuple[bool, str]:
		username, error = self._validate_credentials(username, password)
		if error:
			return False, error
		if not isinstance(first_name, str) or not first_name.strip():
			return False, "El nombre del administrador es obligatorio."
		if not isinstance(last_name, str) or not last_name.strip():
			return False, "El apellido del administrador es obligatorio."
		try:
			with SessionLocal() as session:
				if session.scalar(select(func.count()).select_from(Employee)):
					return False, "Ya existen empleados; configura uno existente."
				employee = Employee(
					first_name=first_name.strip(),
					last_name=last_name.strip(),
					role="Administrator",
					username=username,
					password_hash=self.hash_password(password),
					is_active=True,
				)
				session.add(employee)
				session.commit()
			return True, "Administrador inicial creado correctamente."
		except Exception as error:
			return False, f"No se pudo crear el administrador: {error}"

	@classmethod
	def hash_password(cls, password: str) -> str:
		salt = secrets.token_bytes(16)
		digest = hashlib.pbkdf2_hmac(
			"sha256", password.encode("utf-8"), salt, cls._ITERATIONS
		)
		salt_text = base64.urlsafe_b64encode(salt).decode("ascii").rstrip("=")
		digest_text = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
		return f"{cls._SCHEME}${cls._ITERATIONS}${salt_text}${digest_text}"

	@staticmethod
	def _validate_credentials(username, password):
		username = username.strip() if isinstance(username, str) else ""
		if len(username) < 3 or len(username) > 50:
			return username, "El usuario debe tener entre 3 y 50 caracteres."
		if not isinstance(password, str) or len(password) < 12:
			return username, "La contraseña debe tener al menos 12 caracteres."
		return username, None

	@classmethod
	def verify_password(cls, password: str, encoded_hash: str | None) -> bool:
		if not encoded_hash:
			return False
		try:
			scheme, iterations_text, salt_text, expected_text = encoded_hash.split("$")
			if scheme != cls._SCHEME:
				return False
			padding = "=" * (-len(salt_text) % 4)
			salt = base64.urlsafe_b64decode(salt_text + padding)
			expected = base64.urlsafe_b64decode(
				expected_text + "=" * (-len(expected_text) % 4)
			)
			actual = hashlib.pbkdf2_hmac(
				"sha256", password.encode("utf-8"), salt, int(iterations_text)
			)
			return hmac.compare_digest(actual, expected)
		except (ValueError, TypeError):
			return False