import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

class DatabaseConnection:
    """Clase para gestionar la conexión a la base de datos PostgreSQL usando el patrón Singleton/Context Manager."""

    @staticmethod
    def get_connection():
        try:
            conn = psycopg.connect(
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                row_factory=dict_row  # Retorna resultados como diccionarios en lugar de tuplas
            )
            return conn
        except psycopg.Error as e:
            print(f"Error al conectar a PostgreSQL: {e}")
            raise e