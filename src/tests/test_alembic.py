from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine
from src.config import Settings

def check_alembic_status():
    settings = Settings()
    print(f"Environment: {settings.ENV}")
    print(f"Database URL: {settings.database_url}")
    
    # Create engine
    engine = create_engine(settings.database_url)
    
    # Get current revision in database
    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        current_rev = context.get_current_revision()
        print(f"Current database revision: {current_rev}")
    
    # Get latest revision in migrations
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    head_rev = script.get_current_head()
    print(f"Latest migration revision: {head_rev}")

if __name__ == "__main__":
    check_alembic_status() 