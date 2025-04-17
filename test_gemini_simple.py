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

def test_gemini_data_flow():
    """Test the data flow to Gemini when mentioning @MDIZX ticker"""
    print("Testing data flow to Gemini with @MDIZX mention...")
    
    # Initialize database and services
    db = DatabaseManager()
    session = db.get_session()
    gemini_service = GeminiService()
    
    # Simulate a conversation with @MDIZX mention
    conversation = [
        {"role": "assistant", "content": "Hello! I'm BiL, your Fund of Funds AI assistant. How can I help you today?"},
        {"role": "user", "content": "Tell me about @MDIZX fund performance"}
    ]
    
    # First, print the original conversation
    print("\n=== ORIGINAL CONVERSATION ===")
    for msg in conversation:
        print(f"{msg['role']}: {msg['content'][:50]}...")
    
    # Create a copy of the conversation for enhancement
    conversation_copy = [dict(msg) for msg in conversation]
    
    # Enhance the last message with fund data
    last_message = conversation_copy[-1]['content']
    enhanced_message, was_enhanced, fetched_tickers = gemini_service.enhance_message_with_fund_data(
        session, last_message
    )
    
    if was_enhanced:
        # Replace the last message with the enhanced version
        conversation_copy[-1]['content'] = enhanced_message
        
        # Print the enhanced conversation
        print("\n=== ENHANCED CONVERSATION (WHAT GEMINI RECEIVES) ===")
        for msg in conversation_copy:
            print(f"{msg['role']}: {msg['content'][:50]}...")
            
        # Print the full enhanced message
        print("\n=== FULL ENHANCED MESSAGE ===")
        print(enhanced_message)
    else:
        print("\nMessage was not enhanced with fund data.")
    
    # Clean up
    session.close()

if __name__ == "__main__":
    test_gemini_data_flow()
