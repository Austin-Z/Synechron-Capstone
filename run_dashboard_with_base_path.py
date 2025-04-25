import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Run the Streamlit app with the correct base URL path for local development
os.system("streamlit run src/dashboard/app.py --server.baseUrlPath=dashboard")
