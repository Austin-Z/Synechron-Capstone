from enum import Enum
from pydantic_settings import BaseSettings
from typing import Optional
import os
from pydantic import validator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Environment(Enum):
    DEV = "development"
    PROD = "production"
    TEST = "testing"

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Environment
    env: str = os.getenv("ENV", "development")
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Database
    db_host: str = os.getenv("DB_HOST", "localhost")  # Changed from host.docker.internal to localhost
    db_port: int = int(os.getenv("DB_PORT", "3306"))
    db_name: str = os.getenv("DB_NAME", "fof_analysis")
    db_user: str = os.getenv("DB_USER", "root")
    db_password: str = os.getenv("DB_PASSWORD", "")
    
    # Default database URL (not used directly)
    database_url_default: str = os.getenv(
        "DATABASE_URL", 
        f"mysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )
    
    # API settings
    api_rate_limit: int = int(os.getenv("API_RATE_LIMIT", "10"))
    
    # SEC API settings
    sec_user_agent: str = os.getenv("SEC_USER_AGENT", "")
    
    # OpenFIGI API settings
    openfigi_api_key: Optional[str] = os.getenv("OPENFIGI_API_KEY")
    figi_api_key: Optional[str] = os.getenv("FIGI_API_KEY")
    
    # Gemini API settings
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
    
    # Application Settings
    TEST_DB_NAME: str = "fof_analysis_test"
    LOG_LEVEL: str = "INFO"
    
    @validator('env', pre=True)
    def parse_environment(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v
    
    @property
    def database_url(self) -> str:
        # First check for DATABASE_URL (highest priority)
        railway_url = os.getenv("DATABASE_URL")
        if railway_url:
            return railway_url
        
        # Then check for Railway-specific MySQL variables
        mysql_host = os.getenv('MYSQLHOST')
        mysql_user = os.getenv('MYSQLUSER')
        mysql_password = os.getenv('MYSQLPASSWORD')
        mysql_port = os.getenv('MYSQLPORT')
        mysql_database = os.getenv('MYSQL_DATABASE')
        
        if mysql_host and mysql_password:
            # Construct the URL using Railway's MySQL variables
            return f"mysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"
            
        # Local development/testing
        if self.env == Environment.TEST:
            return f"mysql+mysqlconnector://root@localhost/{self.TEST_DB_NAME}"
        else:
            return f"mysql+mysqlconnector://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        use_enum_values = True 