from sqlalchemy import create_engine, text
from src.config import Settings

def create_database():
    settings = Settings()
    # Connect to MySQL server without database
    engine = create_engine(f"mysql+mysqlconnector://root:@localhost:3306/")
    
    with engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {settings.DB_NAME}"))
        print(f"Database {settings.DB_NAME} created successfully!")

if __name__ == "__main__":
    create_database() 