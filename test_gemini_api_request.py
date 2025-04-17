import os
import sys
import json
from dotenv import load_dotenv
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Import required modules
from src.database.manager import DatabaseManager
from src.services.gemini_service import GeminiService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('gemini_api_test')

# Load environment variables
load_dotenv()

def test_gemini_api_request():
    """Test how data is fed to Gemini API when mentioning @MDIZX ticker"""
    logger.info("Testing Gemini API request with @MDIZX mention...")
    
    # Initialize database and services
    db = DatabaseManager()
    session = db.get_session()
    
    # Create a modified GeminiService class to intercept the API request
    class TestGeminiService(GeminiService):
        def __init__(self):
            super().__init__()
            
        def format_messages(self, messages):
            formatted = super().format_messages(messages)
            logger.info(f"Formatted messages for Gemini API: {json.dumps(formatted, indent=2)}")
            return formatted
            
        def get_response(self, messages, session=None, overlap_data=None):
            # Create a deep copy of the messages to avoid modifying the original
            messages_copy = [dict(msg) for msg in messages]
            
            # Check if we need to enhance the last user message with fund/overlap data
            if session and len(messages_copy) > 0 and messages_copy[-1]['role'] == 'user':
                last_message = messages_copy[-1]['content']
                enhanced_message, was_enhanced, fetched_tickers = self.enhance_message_with_fund_data(
                    session, last_message, overlap_data
                )
                
                if was_enhanced:
                    # Replace the last message with the enhanced version in our copy only
                    messages_copy[-1]['content'] = enhanced_message
                    logger.info("Message was enhanced with fund data")
                    
                    # Show what would be sent to Gemini
                    logger.info("Data that would be sent to Gemini API:")
                    formatted_messages = self.format_messages(messages_copy)
                    
                    # Prepare request payload
                    payload = {
                        "contents": formatted_messages,
                        "generationConfig": {
                            "temperature": 0.7,
                            "topK": 40,
                            "topP": 0.95,
                            "maxOutputTokens": 1024,
                        }
                    }
                    
                    logger.info(f"API payload: {json.dumps(payload, indent=2)}")
                    return "TEST RESPONSE - Not actually calling Gemini API"
            
            return "No enhancement was performed"
    
    # Create our test service
    test_service = TestGeminiService()
    
    # Simulate a conversation with @MDIZX mention
    conversation = [
        {"role": "assistant", "content": "Hello! I'm BiL, your Fund of Funds AI assistant. How can I help you today?"},
        {"role": "user", "content": "Tell me about @MDIZX fund performance"}
    ]
    
    # Get response (this will log the API request details)
    response = test_service.get_response(conversation, session)
    
    logger.info(f"Response: {response}")
    
    # Clean up
    session.close()

if __name__ == "__main__":
    test_gemini_api_request()
