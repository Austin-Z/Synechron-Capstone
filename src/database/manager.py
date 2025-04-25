from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
from src.models.database import Base
from src.utils.logger import setup_logger
from src.config import Settings
import os

class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self):
        self.logger = setup_logger('database_manager')
        self.settings = Settings()
        self._initialize_connection()
        
    def _initialize_connection(self):
        """Initialize database connection from settings."""
        # Use environment variables from .env file with fallbacks
        DB_USER = os.getenv('DB_USER', 'root')
        DB_PASSWORD = os.getenv('DB_PASSWORD', '')
        DB_HOST = os.getenv('DB_HOST', 'localhost')
        DB_PORT = os.getenv('DB_PORT', '3306')
        DB_NAME = os.getenv('DB_NAME', 'fof_analysis')

        # Use DATABASE_URL if provided, otherwise build from components
        DATABASE_URL = os.getenv('DATABASE_URL') or f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        
        # Create engine with proper configuration
        self.engine = create_engine(
            DATABASE_URL,
            pool_recycle=3600,
            pool_pre_ping=True,
            connect_args={
                'connect_timeout': 60
            }
        )
        
        # Create session factory
        self.Session = sessionmaker(bind=self.engine)
        
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(self.engine)
        
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.Session()
        
    def add_with_commit(self, session: Session, obj: Base) -> Optional[Base]:
        """Add an object to the database and commit."""
        try:
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            self.logger.error(f"Error adding to database: {str(e)}")
            session.rollback()
            return None 