from config.database import DatabaseConnection
import psycopg

class BaseModel:
    """Clase base que provee métodos de ejecución SQL reutilizables para los modelos."""

    @classmethod
    def execute_query(cls, query: str, params: tuple = None, fetchone: bool = False, fetchall: bool = False):
        """Ejecuta consultas SQL de lectura o modificación básica."""
        conn = None
        try:
            conn = DatabaseConnection.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                
                if fetchone:
                    result = cursor.fetchone()
                elif fetchall:
                    result = cursor.fetchall()
                else:
                    result = None
                
                conn.commit()
                return result
        except psycopg.Error as e:
            if conn:
                conn.rollback()
            print(f"Error en {cls.__name__}.execute_query: {e}")
            raise e
        finally:
            if conn:
                conn.close()