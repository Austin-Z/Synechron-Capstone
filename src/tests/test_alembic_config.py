from alembic.config import Config
import os

def check_alembic_config():
    print(f"Current directory: {os.getcwd()}")
    print(f"Files in current directory: {os.listdir('.')}")
    
    try:
        config = Config("alembic.ini")
        print("\nAlembic config found!")
        print(f"Script location: {config.get_main_option('script_location')}")
        print(f"SQL Alchemy URL: {config.get_main_option('sqlalchemy.url')}")
    except Exception as e:
        print(f"\nError loading alembic config: {str(e)}")

if __name__ == "__main__":
    check_alembic_config() 