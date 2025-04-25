"""
Service for interacting with Google's Gemini API.
"""
import os
import json
import requests
import re
import asyncio
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from dotenv import load_dotenv
from src.utils.logger import setup_logger
from src.services.fund_service import FundService
from src.collectors.edgar_collector import EdgarCollector
from src.scripts.load_initial_funds import DataLoader

class GeminiService:
    """Service for interacting with Google's Gemini API."""
    
    def __init__(self):
        """Initialize the Gemini service."""
        self.logger = setup_logger('gemini_service')
        
        # Ensure environment variables are loaded
        load_dotenv()
        
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            self.logger.warning("GEMINI_API_KEY not found in environment variables")
            
        # Print the API key (first few characters) for debugging
        if self.api_key:
            self.logger.info(f"GEMINI_API_KEY found: {self.api_key[:5]}...")
        
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        
    def format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Format messages for the Gemini API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            
        Returns:
            Formatted messages for Gemini API
        """
        formatted_messages = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            formatted_messages.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })
        return formatted_messages
    
    def detect_tickers(self, text: str) -> Set[str]:
        """
        Detect potential stock tickers in the message.
        
        Args:
            text: The text to analyze for tickers
            
        Returns:
            Set of potential ticker symbols found in the text
        """
        # First look for explicit @ mentions (e.g., @VFIAX)
        mention_pattern = r'@([A-Z]{1,5}(?:\.[A-Z]{1,2})?)\'b'
        explicit_mentions = set(re.findall(mention_pattern, text))
        
        if explicit_mentions:
            self.logger.info(f"Detected explicit ticker mentions: {explicit_mentions}")
            return explicit_mentions
        
        # If no explicit mentions, fall back to pattern matching
        # Pattern for stock tickers: 1-5 uppercase letters, potentially with a period
        ticker_pattern = r'\b[A-Z]{1,5}(?:\.[A-Z]{1,2})?\b'
        
        # Find all matches
        potential_tickers = set(re.findall(ticker_pattern, text))
        
        # Filter out common words that might be mistaken for tickers
        common_words = {'I', 'A', 'AN', 'THE', 'AND', 'OR', 'BUT', 'IF', 'THEN', 'TO', 'FOR'}
        filtered_tickers = potential_tickers - common_words
        
        self.logger.info(f"Detected potential tickers: {filtered_tickers}")
        return filtered_tickers
        
    def detect_overlap_mention(self, text: str) -> bool:
        """
        Detect if the @overlap keyword is mentioned in the text.
        
        Args:
            text: The text to analyze for the overlap keyword
            
        Returns:
            Boolean indicating if @overlap was mentioned
        """
        # Look for the @overlap keyword
        overlap_pattern = r'@overlap\b'
        overlap_mentioned = bool(re.search(overlap_pattern, text, re.IGNORECASE))
        
        if overlap_mentioned:
            self.logger.info("@overlap keyword detected in message")
            
        return overlap_mentioned
    
    def get_fund_data(self, session, ticker: str) -> Dict[str, Any]:
        """
        Get detailed fund data for a given ticker.
        
        Args:
            session: Database session
            ticker: Fund ticker symbol
            
        Returns:
            Dictionary with fund data
        """
        try:
            # Get fund information
            fund = FundService.get_fund_by_ticker(session, ticker)
            if not fund:
                return {}
            
            # Get holdings data
            holdings_df = FundService.get_holdings_details(session, ticker)
            
            # Get asset allocation
            if fund.filings:
                asset_allocation = FundService.get_asset_allocation(fund.filings[0].holdings)
            else:
                asset_allocation = {}
            
            # Get top holdings
            top_holdings = FundService.get_top_holdings(fund.filings[0].holdings if fund.filings else [])
            
            # Get underlying securities for each top holding (if it's a fund-of-funds)
            underlying_securities = {}
            if fund.fund_type == 'fund_of_funds' and top_holdings:
                for i, holding in enumerate(top_holdings[:10]):  # Limit to top 10 holdings
                    # Fix: Use 'Ticker' (uppercase) instead of 'ticker' (lowercase)
                    if 'Ticker' in holding and holding['Ticker'] and holding['Ticker'] != 'None':
                        ticker = holding['Ticker']
                        self.logger.info(f"Looking up underlying securities for {ticker}")
                        underlying_fund = FundService.get_fund_by_ticker(session, ticker)
                        if underlying_fund and underlying_fund.filings:
                            underlying_top_holdings = FundService.get_top_holdings(underlying_fund.filings[0].holdings)
                            underlying_securities[ticker] = underlying_top_holdings[:10]  # Top 10 underlying securities
            
            # Compile fund data
            fund_data = {
                "ticker": fund.ticker,
                "name": fund.name,
                "fund_type": fund.fund_type,
                "total_assets": fund.filings[0].total_assets if fund.filings else None,
                "filing_date": fund.filings[0].filing_date.strftime("%Y-%m-%d") if fund.filings else None,
                "asset_allocation": asset_allocation,
                "top_holdings": top_holdings[:10],  # Increase to top 10 holdings
                "underlying_securities": underlying_securities,  # Add underlying securities
                "holdings_count": len(fund.filings[0].holdings) if fund.filings else 0
            }
            
            return fund_data
        except Exception as e:
            self.logger.error(f"Error getting fund data: {str(e)}")
            return {}
    
    def format_fund_data_for_prompt(self, fund_data: Dict[str, Any]) -> str:
        """
        Format fund data as a string to be included in the prompt.
        
        Args:
            fund_data: Dictionary with fund data
            
        Returns:
            Formatted string with fund data
        """
        if not fund_data:
            return ""
            
        fund_info = []
        
        # Add fund name and ticker
        ticker = fund_data.get('ticker', 'Unknown')
        fund_name = fund_data.get('name', 'Unknown')
        
        # Add emoji based on fund type
        fund_type = fund_data.get('fund_type', 'Unknown')
        emoji = '📦' if fund_type == 'fund_of_funds' else '📈'
        
        # Start with a clear section header
        fund_info.append(f"===== FUND ANALYSIS: {ticker} =====")
        fund_info.append(f"{emoji} **{ticker}** ({fund_name})")
        
        # Add basic fund information in a structured format
        fund_info.append("\n**FUND SUMMARY:**")
        fund_info.append(f"- **Fund Type:** {fund_type}")
        
        if 'total_assets' in fund_data and fund_data['total_assets']:
            fund_info.append(f"- **Total Assets:** ${fund_data['total_assets']:,.2f}")
            
        if 'filing_date' in fund_data and fund_data['filing_date']:
            fund_info.append(f"- **Filing Date:** {fund_data['filing_date']}")
        
        # Add asset allocation if available
        if 'asset_allocation' in fund_data and fund_data['asset_allocation']:
            fund_info.append("\n**ASSET ALLOCATION:**")
            for asset_class, percentage in fund_data['asset_allocation'].items():
                fund_info.append(f"- {asset_class}: {percentage:.2f}%")
        
        # Add top holdings if available
        if 'top_holdings' in fund_data and fund_data['top_holdings']:
            fund_info.append("\n**TOP HOLDINGS (Top 10):**")
            for i, holding in enumerate(fund_data['top_holdings'][:10], 1):
                holding_name = holding.get('Name', 'Unknown')
                holding_ticker = f" ({holding.get('Ticker')})" if holding.get('Ticker') and holding.get('Ticker') != 'None' else ""
                holding_value = holding.get('Value', 0)
                holding_percentage = holding.get('Percentage', 0)
                
                fund_info.append(f"{i}. {holding_name}{holding_ticker}: {holding_percentage:.2f}% (${holding_value:,.2f})")
        
        # Add underlying securities if available
        if 'underlying_securities' in fund_data and fund_data['underlying_securities']:
            fund_info.append("\n**UNDERLYING SECURITIES BY FUND:**")
            for holding_ticker, securities in fund_data['underlying_securities'].items():
                fund_info.append(f"\n**Securities for {holding_ticker} (Top 10):**")
                for j, security in enumerate(securities[:10], 1):
                    security_name = security.get('Name', 'Unknown')
                    security_ticker = f" ({security.get('Ticker')})" if security.get('Ticker') and security.get('Ticker') != 'None' else ""
                    security_value = security.get('Value', 0)
                    security_percentage = security.get('Percentage', 0)
                    
                    fund_info.append(f"{j}. {security_name}{security_ticker}: {security_percentage:.2f}% (${security_value:,.2f})")
        
        # Add a clear analysis prompt at the end
        fund_info.append("\n**ANALYSIS INSTRUCTIONS:**")
        fund_info.append("1. Analyze the fund composition and structure - this is a fund-of-funds that holds other mutual funds")
        fund_info.append("2. Identify key characteristics of this fund based on its holdings and asset allocation")
        fund_info.append("3. Analyze the specific funds it holds (MRSKX, MEMJX, etc.) and their relative weights")
        fund_info.append("4. Explain how the fund's structure provides diversification through its holdings")
        fund_info.append("5. Provide insights based ONLY on the data above - do not use general knowledge about funds")
        
        return "\n".join(fund_info)
    
    def enhance_message_with_fund_data(self, session, message: str, overlap_data=None) -> Tuple[str, bool, Set[str]]:
        """
        Enhance a message with fund data if tickers are detected and/or overlap data if @overlap is mentioned.
        
        Args:
            session: Database session
            message: The original message
            overlap_data: Optional dictionary containing overlap analysis data from the dashboard
            
        Returns:
            Tuple of (enhanced message, whether enhancement occurred, set of new tickers fetched)
        """
        # Detect tickers in the message
        potential_tickers = self.detect_tickers(message)
        print(f"DEBUG: Detected potential tickers: {potential_tickers}")
        
        # Check if the user is asking about overlap analysis
        overlap_mentioned = "@overlap" in message.lower()
        print(f"DEBUG: Overlap mentioned: {overlap_mentioned}")
        
        # If no tickers and no overlap mentioned, return original message
        if not potential_tickers and not overlap_mentioned:
            return message, False, set()
        
        # Get all valid fund tickers from the database
        all_tickers = set(FundService.get_all_fund_tickers(session))
        print(f"DEBUG: All tickers in database: {all_tickers}")
        
        # Find the intersection of potential tickers and actual fund tickers
        valid_tickers = potential_tickers.intersection(all_tickers)
        print(f"DEBUG: Valid tickers already in database: {valid_tickers}")
        
        # Check for new tickers that need to be fetched
        new_tickers = potential_tickers - all_tickers
        fetched_tickers = set()
        
        if new_tickers:
            self.logger.info(f"Detected new tickers not in database: {new_tickers}")
            print(f"DEBUG: Detected new tickers not in database: {new_tickers}")
            # Fetch and store data for new tickers
            fetched_tickers = self.fetch_and_store_new_tickers(session, new_tickers)
            print(f"DEBUG: Successfully fetched new tickers: {fetched_tickers}")
            # Add successfully fetched tickers to valid tickers
            valid_tickers.update(fetched_tickers)
        
        # Initialize enhancement flags
        has_fund_data = False
        has_overlap_data = False
        
        # Prepare sections for the enhanced message
        message_sections = [message]
        
        # Add fund data if valid tickers were found
        if valid_tickers:
            # Retrieve and format fund data for each valid ticker
            fund_data_sections = []
            for ticker in valid_tickers:
                fund_data = self.get_fund_data(session, ticker)
                if fund_data:
                    fund_data_sections.append(self.format_fund_data_for_prompt(fund_data))
            
            if fund_data_sections:
                # Join the fund data sections with double newlines
                joined_sections = "\n\n".join(fund_data_sections)
                
                # Add fund data section to message with clearer instructions
                message_sections.append("REFERENCE DATA - FUND INFORMATION:")
                message_sections.append("I've detected references to the following funds. The data below is accurate and should be used as the primary source for your response:")
                message_sections.append(joined_sections)
                has_fund_data = True
                self.logger.info(f"Enhanced message with data for tickers: {valid_tickers}")
        
        # Add overlap data if @overlap was mentioned and overlap_data is provided
        if overlap_mentioned and overlap_data:
            overlap_section = self.format_overlap_data_for_prompt(overlap_data)
            if overlap_section:
                message_sections.append("REFERENCE DATA - OVERLAP ANALYSIS:")
                message_sections.append("I've detected a request for overlap analysis. The data below is accurate and should be used as the primary source for your response:")
                message_sections.append(overlap_section)
                has_overlap_data = True
                self.logger.info("Enhanced message with overlap analysis data")
        
        # If no enhancements were made, return the original message
        if not has_fund_data and not has_overlap_data:
            return message, False, fetched_tickers
        
        # Extract the original user question
        original_question = message
        
        # Create a completely restructured message that separates the question from the data
        restructured_sections = [
            "===== SYSTEM INSTRUCTION =====\n",
            "You are BiL, a Fund of Funds AI assistant with access to accurate, up-to-date fund data. You MUST ANALYZE the reference data provided below and NOT rely on your general knowledge about funds.",
            "\n===== REFERENCE DATA =====\n"
        ]
        
        # Add all the data sections
        restructured_sections.extend(message_sections)
        
        # Add the user's original question at the end
        restructured_sections.append("\n===== USER QUESTION =====\n")
        restructured_sections.append(original_question)
        
        # Add final instruction with very explicit guidance
        restructured_sections.append("\n===== CRITICAL INSTRUCTION =====\n")
        restructured_sections.append("1. Your response MUST be based EXCLUSIVELY on the REFERENCE DATA provided above.")
        restructured_sections.append("2. DO NOT use any general knowledge about funds that contradicts the reference data.")
        restructured_sections.append("3. IMPORTANT: You MUST ANALYZE the fund data provided above. If the data shows a fund is a fund-of-funds, explain its structure and holdings.")
        restructured_sections.append("4. For each fund mentioned, provide a detailed analysis of its composition, holdings, and asset allocation.")
        restructured_sections.append("5. Explain what makes this fund unique based on the data provided.")
        restructured_sections.append("6. NEVER say you don't have information about a fund when the data is provided above.")
        
        # Combine all sections with newlines
        enhanced_message = "\n".join(restructured_sections)
        
        return enhanced_message, True, fetched_tickers
    
    def fetch_and_store_new_tickers(self, session, tickers: Set[str]) -> Set[str]:
        """
        Fetch data for new tickers from SEC EDGAR and store in database.
        
        Args:
            session: Database session
            tickers: Set of ticker symbols to fetch
            
        Returns:
            Set of successfully fetched and stored tickers
        """
        self.logger.info(f"Attempting to fetch data for new tickers: {tickers}")
        print(f"DEBUG: Attempting to fetch data for new tickers: {tickers}")
        successful_tickers = set()
        
        # Convert set to list for processing
        ticker_list = list(tickers)
        
        try:
            # Create data loader
            data_loader = DataLoader()
            print(f"DEBUG: Created DataLoader instance")
            
            # Run the async load_funds method using asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                print(f"DEBUG: Starting to load funds: {ticker_list}")
                results = loop.run_until_complete(data_loader.load_funds(ticker_list))
                print(f"DEBUG: Load funds results: {results}")
            finally:
                loop.close()
            
            # Add successful tickers to the set
            successful_tickers.update(results.get('success', []))
            successful_tickers.update(results.get('updated', []))
            
            self.logger.info(f"Successfully fetched and stored data for tickers: {successful_tickers}")
            print(f"DEBUG: Successfully fetched and stored data for tickers: {successful_tickers}")
            
            # If there were failures, log them
            failed_tickers = set(ticker_list) - successful_tickers
            if failed_tickers:
                self.logger.warning(f"Failed to fetch data for tickers: {failed_tickers}")
                print(f"DEBUG: Failed to fetch data for tickers: {failed_tickers}")
                
                # Check if the failed tickers might be ETFs or other securities without NPORT-P filings
                for ticker in failed_tickers:
                    print(f"DEBUG: {ticker} might be an ETF or other security type without NPORT-P filings")
                    self.logger.info(f"{ticker} might be an ETF or other security type without NPORT-P filings")
                
            return successful_tickers
            
        except Exception as e:
            self.logger.error(f"Error fetching and storing new tickers: {str(e)}")
            print(f"DEBUG ERROR: Error fetching and storing new tickers: {str(e)}")
            import traceback
            print(f"DEBUG TRACEBACK: {traceback.format_exc()}")
            return set()
    
    def format_overlap_data_for_prompt(self, overlap_data: Dict[str, Any]) -> str:
        """
        Format overlap analysis data as a string to be included in the prompt.
        
        Args:
            overlap_data: Dictionary with overlap analysis data
            
        Returns:
            Formatted string with overlap analysis data
        """
        if not overlap_data:
            return ""
        
        # Format the overlap data as a string
        overlap_info = [
            "--- OVERLAP ANALYSIS DATA ---"
        ]
        
        # Add selected funds
        if 'selected_funds' in overlap_data:
            overlap_info.append(f"Selected Funds: {', '.join(overlap_data['selected_funds'])}")
        
        # Add fund types if available
        if 'fund_types' in overlap_data:
            overlap_info.append("\nFund Types:")
            for fund, fund_type in overlap_data['fund_types'].items():
                fund_type_icon = "📦" if fund_type == "fund_of_funds" else "📈"
                overlap_info.append(f"- {fund}: {fund_type_icon} {fund_type}")
        
        # Add overlap metrics if available
        if 'metrics' in overlap_data:
            metrics = overlap_data['metrics']
            overlap_info.append("\nOverlap Metrics:")
            if 'overlap_count' in metrics:
                overlap_info.append(f"- Total Overlapping Holdings: {metrics['overlap_count']}")
            if 'total_redundant_value' in metrics:
                overlap_info.append(f"- Total Redundant Value: ${metrics['total_redundant_value']:,.2f}")
            if 'max_overlap' in metrics:
                overlap_info.append(f"- Maximum Overlap: {metrics['max_overlap']} funds")
        
        # Add detailed overlaps if available
        if 'detailed_overlaps' in overlap_data:
            overlaps = overlap_data['detailed_overlaps']
            overlap_info.append("\nTop Overlapping Holdings:")
            # Sort by number of funds (descending)
            sorted_overlaps = sorted(overlaps.items(), key=lambda x: len(x[1]['funds']), reverse=True)
            # Take top 10 for brevity
            for name, data in sorted_overlaps[:10]:
                overlap_info.append(f"- {name}: Found in {len(data['funds'])} funds ({', '.join(data['funds'])}), Total Value: ${data['total_value']:,.2f}")
        
        # Add overlap matrix summary if available
        if 'matrix' in overlap_data:
            matrix = overlap_data['matrix']
            overlap_info.append("\nOverlap Matrix Summary:")
            for fund1 in matrix.index:
                for fund2 in matrix.columns:
                    if fund1 != fund2 and matrix.loc[fund1, fund2] > 0:
                        overlap_info.append(f"- {fund1} and {fund2}: {matrix.loc[fund1, fund2]} overlapping holdings")
        
        overlap_info.append("----------------------------")
        
        return "\n".join(overlap_info)

    def get_response(self, messages: List[Dict[str, str]], session=None, overlap_data=None) -> str:
        """
        Get a response from Gemini API based on conversation history.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            session: Optional database session for fund data retrieval
            overlap_data: Optional dictionary containing overlap analysis data
            
        Returns:
            Response text from Gemini
        """
        if not self.api_key:
            return "Error: Gemini API key not configured. Please set the GEMINI_API_KEY environment variable."
        
        try:
            # Create a deep copy of the messages to avoid modifying the original
            messages_copy = [dict(msg) for msg in messages]
            
            # Check if we need to enhance the last user message with fund/overlap data
            enhanced_data = ""
            original_question = ""
            was_enhanced = False
            
            if session and len(messages_copy) > 0 and messages_copy[-1]['role'] == 'user':
                original_question = messages_copy[-1]['content']
                enhanced_message, was_enhanced, fetched_tickers = self.enhance_message_with_fund_data(
                    session, original_question, overlap_data
                )
                
                if was_enhanced:
                    # We'll use a completely different approach with the Gemini API
                    logging.info(f"Enhanced message with data for tickers: {fetched_tickers}")
            
            # Format messages for Gemini API
            formatted_messages = []
            
            if was_enhanced:
                # Add a system message first to set the context
                formatted_messages.append({
                    "role": "model",
                    "parts": [{"text": "I am BiL, a Fund of Funds AI assistant. I will only use the reference data you provide to answer questions."}]
                })
                
                # Add all previous messages except the last one
                for i in range(len(messages_copy) - 1):
                    formatted_messages.append({
                        "role": messages_copy[i]['role'],
                        "parts": [{"text": messages_copy[i]['content']}]
                    })
                
                # Add the enhanced message as the last user message
                formatted_messages.append({
                    "role": "user",
                    "parts": [{"text": enhanced_message}]
                })
            else:
                # No enhancement, just use the original messages
                for msg in messages_copy:
                    formatted_messages.append({
                        "role": msg['role'],
                        "parts": [{"text": msg['content']}]
                    })
            
            # Make API request to Gemini
            try:
                import google.generativeai as genai
                
                # Configure the Gemini API
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel('gemini-2.0-flash')
                
                # Generate content
                response = model.generate_content(formatted_messages)
                return response.text
            except ImportError:
                # Fall back to using requests if google.generativeai is not available
                payload = {
                    "contents": formatted_messages,
                    "generationConfig": {
                        "temperature": 0.7,
                        "topK": 40,
                        "topP": 0.95,
                        "maxOutputTokens": 4098,
                    }
                }
                
                response = requests.post(
                    f"{self.api_url}?key={self.api_key}",
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(payload)
                )
                
                # Check for successful response
                if response.status_code == 200:
                    response_json = response.json()
                    
                    # Extract text from response
                    if (response_json.get("candidates") and 
                        response_json["candidates"][0].get("content") and 
                        response_json["candidates"][0]["content"].get("parts")):
                        # Get the raw text response
                        raw_response = response_json["candidates"][0]["content"]["parts"][0]["text"]
                        
                        # Return the sanitized response
                        return raw_response
                    else:
                        self.logger.error(f"Unexpected response structure: {response_json}")
                        return "Sorry, I couldn't generate a response. Please try again."
                else:
                    self.logger.error(f"API error: {response.status_code} - {response.text}")
                    return f"Sorry, there was an error communicating with the AI service. Status code: {response.status_code}"
        
        except Exception as e:
            self.logger.exception(f"Error calling Gemini API: {str(e)}")
            return f"Sorry, an error occurred: {str(e)}"
    
    def get_response_for_single_message(self, message: str, session=None, overlap_data=None) -> str:
        """
        Get a response for a single message without conversation history.
        
        Args:
            message: The user's message
            session: Optional database session for fund data retrieval
            overlap_data: Optional dictionary containing overlap analysis data
            
        Returns:
            Response text from Gemini
        """
        messages = [{"role": "user", "content": message}]
        return self.get_response(messages, session, overlap_data)
