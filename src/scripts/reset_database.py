from src.database.manager import DatabaseManager
from src.models.database import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database():
    """Drop all tables and recreate them."""
    db = DatabaseManager()
    engine = db.engine
    
    try:
        logger.info("Dropping all tables...")
        Base.metadata.drop_all(engine)
        logger.info("Recreating tables...")
        Base.metadata.create_all(engine)
        logger.info("Database reset complete!")
    except Exception as e:
        logger.error(f"Error resetting database: {str(e)}")

if __name__ == "__main__":
    reset_database() 