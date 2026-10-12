# Operación del DMS

## Preparar el entorno

```bash
python3 -m venv venv
./venv/bin/python -m pip install -r requirements.txt
```

Configure `config/.env` localmente con `DB_HOST`, `DB_PORT`, `DB_NAME`,
`DB_USER` y `DB_PASSWORD`. No agregue ese archivo al repositorio.

## Crear o actualizar la base

Haga un respaldo de PostgreSQL antes de la primera actualización. Ejecute
`alembic upgrade head` una sola vez por base de datos, con una cuenta que pueda
alterar el esquema. Por ejemplo:

```bash
pg_dump -Fc -h localhost -p 5432 -U postgres -d autos_amistosos -f autos_amistosos_before_migration.dump
./venv/bin/alembic upgrade head
```

La migración conserva las facturas existentes como `completed`. Agrega estados
de venta, auditoría de aprobación/cancelación y campos de credenciales. Si
detecta más de una venta activa para el mismo VIN, se detiene sin borrar datos;
revise esos casos y vuelva a ejecutar la migración.

Cada equipo cliente debe usar la misma base y una versión compatible de la
aplicación. Los clientes no ejecutan migraciones al arrancar; la aplicación
muestra un error explícito si la revisión instalada no está aplicada.

## Configurar cuentas

Después de migrar, configure cada cuenta desde una terminal local:

```bash
./venv/bin/python -m utils.provision_employee
```

En una base vacía, el asistente crea el primer `Administrator`. En una base con
empleados, muestra sus IDs y roles para asignar credenciales al empleado
correcto. Las contraseñas se solicitan de forma oculta y se almacenan con hash
PBKDF2.

Roles admitidos por el flujo actual: `Salesperson` registra ventas;
`Manager` y `Administrator` revisan, rechazan o cancelan ventas. Rechazar o
cancelar conserva la factura y libera el vehículo.

## Iniciar y probar

```bash
./venv/bin/python main.py
./venv/bin/python -m unittest discover -s tests
```

El impuesto se mantiene provisionalmente en 13% y los importes se presentan en
USD. La tasa y la composición gravable están centralizadas en
`utils/sales_calculator.py`.

## Límite de seguridad

Esta aplicación de escritorio se conecta directamente a PostgreSQL, por lo que
cada dispositivo que la ejecute necesita credenciales de base de datos. Los
roles limitan las operaciones desde la interfaz y el controlador, pero no
sustituyen permisos de base de datos frente a un usuario que conozca esas
credenciales. Para equipos fuera de una red interna de confianza, conviene
migrar el acceso a un servicio/API intermedio.