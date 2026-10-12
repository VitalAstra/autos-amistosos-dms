"""Configuración de negocio configurable mediante el archivo de entorno."""

import os
from decimal import Decimal, InvalidOperation
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent / ".env")

try:
	SALES_TAX_RATE = Decimal(os.getenv("SALES_TAX_RATE", "0.13"))
except InvalidOperation as error:
	raise RuntimeError("SALES_TAX_RATE debe ser un número válido.") from error

if not SALES_TAX_RATE.is_finite() or not Decimal("0") <= SALES_TAX_RATE <= Decimal("1"):
	raise RuntimeError("SALES_TAX_RATE debe estar entre 0 y 1.")
