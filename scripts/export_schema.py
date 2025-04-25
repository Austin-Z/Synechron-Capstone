from sqlalchemy import create_engine, MetaData
from src.models.database import Base
import os
from dotenv import load_dotenv

def export_schema():
    load_dotenv()
    
    # Get database URL from environment
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME', 'fof_analysis')
    
    DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # Create engine
    engine = create_engine(DATABASE_URL)
    
    # Generate schema
    metadata = Base.metadata
    
    # Export schema to file
    with open('schema.sql', 'w') as f:
        for table in metadata.sorted_tables:
            f.write(f"-- Table: {table.name}\n")
            f.write(str(table.schema) + "\n\n")
            
if __name__ == "__main__":
    export_schema() 