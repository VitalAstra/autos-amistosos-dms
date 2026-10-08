"""Configuración SQLAlchemy 2.0 y fábrica de sesiones PostgreSQL."""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
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
	"""Crea las tablas declaradas en los modelos que aún no existan."""
	from importlib import import_module

	for module_name in (
		"models.customer",
		"models.employee",
		"models.sales_invoice",
		"models.vehicle",
	):
		import_module(module_name)
	Base.metadata.create_all(bind=engine)
