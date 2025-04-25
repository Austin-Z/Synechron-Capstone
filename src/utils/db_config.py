from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.database import Base
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseConnection:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        db_url = os.getenv('DATABASE_URL', 'mysql://user:password@localhost/fof_analysis')
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def create_tables(self):
        Base.metadata.create_all(self.engine)
        
    def get_session(self):
        return self.SessionLocal() 