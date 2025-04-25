from sqlalchemy import create_engine, MetaData, inspect, text
from src.models.database import Base
import os
from dotenv import load_dotenv

def export_database():
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
    inspector = inspect(engine)
    
    # Export schema and data
    with open('database_backup.sql', 'w') as f:
        with engine.connect() as connection:
            # Write schema
            for table_name in inspector.get_table_names():
                # Get create table statement
                result = connection.execute(text(f"SHOW CREATE TABLE {table_name}"))
                create_stmt = result.fetchone()[1]
                f.write(f"{create_stmt};\n\n")
                
                # Get data insert statements
                result = connection.execute(text(f"SELECT * FROM {table_name}"))
                rows = result.fetchall()
                if rows:
                    columns = result.keys()
                    for row in rows:
                        values = [f"'{str(val).replace(chr(39), chr(39)+chr(39))}'" if val is not None else 'NULL' for val in row]
                        f.write(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)});\n")
                f.write("\n")

if __name__ == "__main__":
    export_database() 