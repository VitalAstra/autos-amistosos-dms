from alembic import context

from config.database import Base, engine
from models.customer import Customer
from models.employee import Employee
from models.sales_addons import (
	Customization,
	Financing,
	Insurance,
	Survey,
	TradeIn,
	Warranty,
)
from models.sales_invoice import SalesInvoice
from models.vehicle import Vehicle

config = context.config
config.set_main_option(
	"sqlalchemy.url",
	engine.url.render_as_string(hide_password=False).replace("%", "%%"),
)
target_metadata = Base.metadata


def run_migrations_offline():
	context.configure(
		url=config.get_main_option("sqlalchemy.url"),
		target_metadata=target_metadata,
		literal_binds=True,
		dialect_opts={"paramstyle": "named"},
		compare_type=True,
	)
	with context.begin_transaction():
		context.run_migrations()


def run_migrations_online():
	with engine.connect() as connection:
		context.configure(
			connection=connection,
			target_metadata=target_metadata,
			compare_type=True,
		)
		with context.begin_transaction():
			context.run_migrations()


if context.is_offline_mode():
	run_migrations_offline()
else:
	run_migrations_online()