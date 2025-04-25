import os
import sys
from sqlalchemy import inspect

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.manager import DatabaseManager

def inspect_tables():
    # Initialize database connection
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # Get inspector
        inspector = inspect(session.bind)
        
        # Get all table names
        tables = inspector.get_table_names()
        print(f"Tables in database: {tables}")
        
        # Check if the institutional tables exist
        if 'institute13f' in tables:
            print("\nColumns in institute13f:")
            for column in inspector.get_columns('institute13f'):
                print(f"- {column['name']}: {column['type']}")
                
        if 'institutional_holdings' in tables:
            print("\nColumns in institutional_holdings:")
            for column in inspector.get_columns('institutional_holdings'):
                print(f"- {column['name']}: {column['type']}")
                
        # Check for foreign keys
        if 'institute13f' in tables:
            print("\nForeign keys in institute13f:")
            for fk in inspector.get_foreign_keys('institute13f'):
                print(f"- {fk}")
                
        if 'institutional_holdings' in tables:
            print("\nForeign keys in institutional_holdings:")
            for fk in inspector.get_foreign_keys('institutional_holdings'):
                print(f"- {fk}")
    
    except Exception as e:
        print(f"Error inspecting database: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    inspect_tables()
