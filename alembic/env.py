from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from src.models.database import Base
from src.config import Settings
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('alembic.env')

# Prioritize DATABASE_URL environment variable for Railway deployment
database_url = os.getenv('DATABASE_URL')

# Check for Railway-specific MySQL variables
if not database_url:
    mysql_host = os.getenv('MYSQLHOST')
    mysql_user = os.getenv('MYSQLUSER')
    mysql_password = os.getenv('MYSQLPASSWORD')
    mysql_port = os.getenv('MYSQLPORT')
    mysql_database = os.getenv('MYSQL_DATABASE')
    
    if mysql_host and mysql_password:
        logger.info(f"Railway MySQL variables found, constructing database URL")
        database_url = f"mysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"

# Fall back to Settings if no Railway variables are available
if not database_url:
    logger.info("No Railway database variables found, using Settings")
    settings = Settings()
    database_url = settings.database_url

logger.info(f"Using database URL: {database_url}")

# this is the Alembic Config object
config = context.config

# Override sqlalchemy.url with our configured URL
config.set_main_option('sqlalchemy.url', database_url)

# Interpret the config file for Python logging
fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata 

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    logger.info("Running offline migrations")
    url = database_url
    context.configure(
        url=url,
        target_metadata=Base.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    logger.info("Running online migrations")
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = database_url
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=Base.metadata
        )
        logger.info("Starting migration")
        with context.begin_transaction():
            context.run_migrations()
        logger.info("Migration complete")

if context.is_offline_mode():
    logger.info("Running in offline mode")
    run_migrations_offline()
else:
    logger.info("Running in online mode")
    run_migrations_online() 