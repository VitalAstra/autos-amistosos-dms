"""Configura credenciales iniciales desde una terminal local segura."""

import sys
from getpass import getpass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from controllers.auth_controller import AuthController


def main():
	auth = AuthController()
	employees = auth.list_employees_for_provisioning()
	if not employees:
		first_name = input("Nombre del primer administrador: ").strip()
		last_name = input("Apellido: ").strip()
		username = input("Nombre de usuario: ").strip()
		password = getpass("Contraseña (mínimo 12 caracteres): ")
		confirmation = getpass("Confirma la contraseña: ")
		if password != confirmation:
			print("Las contraseñas no coinciden.")
			return 1
		success, message = auth.bootstrap_initial_admin(
			first_name, last_name, username, password
		)
		print(message)
		return 0 if success else 1

	print("Empleados disponibles:")
	for employee in employees:
		status = "activo" if employee.is_active else "inactivo"
		account = employee.username or "sin usuario"
		print(
			f"  {employee.employee_id}: {employee.first_name} "
			f"{employee.last_name} ({employee.role}; {status}; {account})"
		)
	try:
		employee_id = int(input("ID del empleado que configurar: ").strip())
	except ValueError:
		print("El ID debe ser un número entero.")
		return 1

	username = input("Nombre de usuario: ").strip()
	password = getpass("Contraseña (mínimo 12 caracteres): ")
	confirmation = getpass("Confirma la contraseña: ")
	if password != confirmation:
		print("Las contraseñas no coinciden.")
		return 1

	success, message = auth.set_credentials(employee_id, username, password)
	print(message)
	return 0 if success else 1


if __name__ == "__main__":
	raise SystemExit(main())