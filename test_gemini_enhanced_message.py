import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Import required modules
from src.database.manager import DatabaseManager
from src.services.gemini_service import GeminiService

# Load environment variables
load_dotenv()

def test_enhanced_message():
    """Test the enhanced message structure for Gemini with @MDIZX ticker"""
    print("Testing enhanced message structure with @MDIZX mention...")
    
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
        # Write the enhanced message to a file for easier viewing
        with open("enhanced_message.txt", "w") as f:
            f.write(enhanced_message)
        
        print("\nEnhanced message has been written to enhanced_message.txt")
        
        # Print the first 500 characters to give a preview
        preview_length = 500
        print(f"\nPreview of enhanced message (first {preview_length} characters):")
        print("=" * 80)
        print(enhanced_message[:preview_length])
        print("=" * 80)
        print(f"...and {len(enhanced_message) - preview_length} more characters")
    else:
        print("\nMessage was not enhanced with fund data.")
    
    # Clean up
    session.close()

if __name__ == "__main__":
    test_enhanced_message()
