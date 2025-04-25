from sqlalchemy import create_engine, text
from src.config import Settings
import traceback

def test_db_connection():
    try:
        # Print environment info
        settings = Settings()
        print("Settings loaded successfully")
        print(f"Environment: {settings.ENV}")
        print(f"Testing connection to: {settings.database_url}")
        
        # Try database connection
        print("\nAttempting database connection...")
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            print("Connection established!")
            
            # Test basic query
            result = conn.execute(text("SELECT 1"))
            print("Basic query successful!")
            
            # Check tables
            result = conn.execute(text("""
                SHOW TABLES
            """))
            tables = result.fetchall()
            print("\nExisting tables:")
            for table in tables:
                print(f"- {table[0]}")
            
            # Check if alembic_version table exists
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'alembic_version'
            """))
            count = result.scalar()
            print(f"\nAlembic version table exists: {count > 0}")
            
            if count > 0:
                result = conn.execute(text("SELECT version_num FROM alembic_version"))
                version = result.scalar()
                print(f"Current version: {version}")
                
    except Exception as e:
        print(f"\nError occurred:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("\nTraceback:")
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting database connection test...")
    test_db_connection()
    print("Test complete!") 