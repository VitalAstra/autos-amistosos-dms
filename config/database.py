"""Configuración SQLAlchemy 2.0 y fábrica de sesiones PostgreSQL."""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, inspect
from sqlalchemy.orm import DeclarativeBase, sessionmaker


load_dotenv(Path(__file__).resolve().parent / ".env")


def _database_url() -> URL:
	required_variables = ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD")
	missing_variables = [
		name for name in required_variables if not os.getenv(name)
	]
	if missing_variables:
		missing = ", ".join(missing_variables)
		raise RuntimeError(
			f"Faltan variables de configuración de PostgreSQL: {missing}"
		)

	return URL.create(
		drivername="postgresql+psycopg",
		username=os.environ["DB_USER"],
		password=os.environ["DB_PASSWORD"],
		host=os.environ["DB_HOST"],
		port=int(os.getenv("DB_PORT", "5432")),
		database=os.environ["DB_NAME"],
	)


engine = create_engine(_database_url(), pool_pre_ping=True)


class Base(DeclarativeBase):
	pass


SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
	"""Valida que todos los modelos del dominio estén presentes en la base de datos."""
	from importlib import import_module

	for module_name in (
		"models.customer",
		"models.employee",
		"models.sales_invoice",
		"models.sales_addons",
		"models.vehicle",
	):
		import_module(module_name)

	inspector = inspect(engine)
	required_tables = {
		"customer",
		"employee",
		"vehicle",
		"sales_invoice",
		"financing",
		"trade_in",
		"customization",
		"insurance",
		"warranty",
		"survey",
	}
	missing_tables = sorted(required_tables - set(inspector.get_table_names()))
	if missing_tables:
		raise RuntimeError(
			"No se encontró la estructura requerida en PostgreSQL: "
			+ ", ".join(missing_tables)
		)

	missing_columns = []
	for table_name in sorted(required_tables):
		expected_columns = {
			column.name for column in Base.metadata.tables[table_name].columns
		}
		actual_columns = {
			column["name"] for column in inspector.get_columns(table_name)
		}
		missing_columns.extend(
			f"{table_name}.{column_name}"
			for column_name in sorted(expected_columns - actual_columns)
		)
	if missing_columns:
		raise RuntimeError(
			"El esquema de PostgreSQL está desactualizado; faltan columnas: "
			+ ", ".join(missing_columns)
			+ ". Haz un respaldo y ejecuta `alembic upgrade head` desde la "
			"carpeta del proyecto."
		)
