from src.database.manager import DatabaseManager
from src.config import Settings

def test_database_connection():
    # Print current settings
    settings = Settings()
    print(f"Environment: {settings.ENV}")
    print(f"Database URL: {settings.database_url}")
    
    # Try to connect and create tables
    try:
        db = DatabaseManager()
        db.create_tables()
        print("Successfully created tables!")
        
        # Test session
        session = db.get_session()
        print("Successfully created session!")
        session.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_database_connection() 