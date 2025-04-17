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
        # Print the structure of the enhanced message
        print("\n=== ENHANCED MESSAGE STRUCTURE ===")
        # Print just the first 100 characters of each line
        lines = enhanced_message.split('\n')
        print(f"Total lines: {len(lines)}")
        
        # Print first 10 lines
        print("\nFirst 10 lines:")
        for i in range(min(10, len(lines))):
            # Replace emoji characters with [EMOJI] to avoid encoding issues
            line = lines[i].encode('ascii', 'replace').decode('ascii')
            print(f"Line {i+1}: {line[:100]}" + ("..." if len(line) > 100 else ""))
        
        # Print last 10 lines
        print("\nLast 10 lines:")
        for i in range(max(0, len(lines)-10), len(lines)):
            # Replace emoji characters with [EMOJI] to avoid encoding issues
            line = lines[i].encode('ascii', 'replace').decode('ascii')
            print(f"Line {i+1}: {line[:100]}" + ("..." if len(line) > 100 else ""))
    else:
        print("\nMessage was not enhanced with fund data.")
    
    # Clean up
    session.close()

if __name__ == "__main__":
    test_enhanced_message()
