import os
import sys
from dotenv import load_dotenv
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Import required modules
from src.database.manager import DatabaseManager
from src.services.gemini_service import GeminiService

# Load environment variables
load_dotenv()

def test_ticker_mention():
    """Test what data is retrieved when mentioning @MDIZX ticker"""
    print("Testing ticker mention for @MDIZX...")
    
    # Initialize database and services
    db = DatabaseManager()
    session = db.get_session()
    gemini_service = GeminiService()
    
    # Simulate a user message with @MDIZX mention
    test_message = "Tell me about @MDIZX fund performance"
    
    # Call the enhance_message_with_fund_data method
    enhanced_message, was_enhanced, fetched_tickers = gemini_service.enhance_message_with_fund_data(
        session, test_message
    )
    
    # Print results
    print(f"\nOriginal message: {test_message}")
    print(f"Was enhanced: {was_enhanced}")
    print(f"Fetched tickers: {fetched_tickers}")
    
    if was_enhanced:
        print("\n--- ENHANCED MESSAGE START ---")
        print(enhanced_message)
        print("--- ENHANCED MESSAGE END ---")
    else:
        print("\nMessage was not enhanced with fund data.")
    
    # Clean up
    session.close()

if __name__ == "__main__":
    test_ticker_mention()
