import streamlit as st
import requests
from datetime import datetime
import os
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px
from sec_edgar_api import EdgarClient
import plotly.graph_objects as go
import sys
import traceback
import html
import base64
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Now import with the correct path
from src.database.manager import DatabaseManager
from src.services.fund_service import FundService
from src.services.gemini_service import GeminiService
from src.services.institutional_service import InstitutionalService
from src.dashboard.components.fund_structure import render_fund_structure
from src.dashboard.components.portfolio_analysis import render_portfolio_analysis
from src.dashboard.components.institutional_holdings import render_institutional_holdings_analysis

# Load environment variables
load_dotenv()

# Initialize
db = DatabaseManager()
session = db.get_session()
gemini_service = GeminiService()

# Get all fund tickers for the @ mention feature, prioritizing fund-of-funds
all_funds = FundService.get_funds_with_metadata(session)

# Separate fund-of-funds from other funds
fof_tickers = []
other_tickers = []

for fund in all_funds:
    if fund['ticker']:
        # Check if this is a fund of funds
        fund_obj = FundService.get_fund_by_ticker(session, fund['ticker'])
        if fund_obj and fund_obj.fund_type == 'fund_of_funds':
            fof_tickers.append(fund['ticker'])
        else:
            other_tickers.append(fund['ticker'])

# Combine the lists with fund-of-funds first
all_tickers = fof_tickers + other_tickers

# Store in session state for the @ mention feature
if 'available_tickers' not in st.session_state:
    st.session_state.available_tickers = json.dumps(all_tickers)
    st.session_state.fof_tickers = json.dumps(fof_tickers)

# Debug output to verify tickers are loaded
print(f"Available tickers: {all_tickers[:5]}...")  # Show first 5 tickers
print(f"Fund-of-funds tickers: {fof_tickers}")  # Show all fund-of-funds tickers

def fetch_fund_data(search_type, search_value):
    """Fetch fund data from SEC EDGAR"""
    user_agent = os.getenv("SEC_USER_AGENT")
    headers = {
        'User-Agent': user_agent,
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'data.sec.gov'
    }

    try:
        if search_type == "CIK":
            # Format CIK to 10 digits with leading zeros
            cik = str(search_value).zfill(10)
            
            # First, get basic company info
            company_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            response = requests.get(company_url, headers=headers)
            
            if response.status_code == 200:
                company_data = response.json()
                recent_filings = company_data.get('filings', {}).get('recent', {})
                
                # Filter for NPORT-P filings
                nport_filings = []
                if recent_filings:
                    for idx, form in enumerate(recent_filings.get('form', [])):
                        if form == 'NPORT-P':
                            nport_filings.append({
                                'accessionNumber': recent_filings['accessionNumber'][idx],
                                'filingDate': recent_filings['filingDate'][idx],
                                'reportDate': recent_filings['reportDate'][idx],
                                'form': form
                            })
                
                if nport_filings:
                    return {
                        'fund_info': {
                            'name': company_data.get('name', 'N/A'),
                            'cik': cik,
                            'sic': company_data.get('sicDescription', 'N/A'),
                            'fiscalYearEnd': company_data.get('fiscalYearEnd', 'N/A'),
                            'exchanges': company_data.get('exchanges', ['N/A']),
                            'entityType': company_data.get('entityType', 'N/A')
                        },
                        'filing': nport_filings[0],  # Most recent filing
                        'holdings': nport_filings
                    }
                else:
                    st.warning(f"No NPORT-P filings found for CIK: {search_value}")
                    return None
            else:
                st.error(f"Error accessing SEC API: {response.status_code}")
                return None
            
        else:  # CUSIP search
            st.warning("CUSIP search not yet implemented")
            return None
            
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return None

def prepare_holdings_data(holdings_df: pd.DataFrame) -> pd.DataFrame:
    """Add Value_Numeric column and other necessary transformations."""
    if holdings_df.empty:
        return holdings_df
    
    df = holdings_df.copy()
    
    # Check if Value column exists
    if 'Value' not in df.columns:
        print(f"Warning: 'Value' column not found in holdings data. Available columns: {df.columns.tolist()}")
        # Create a placeholder Value_Numeric column with zeros
        df['Value_Numeric'] = 0.0
        return df
    
    # Handle different data formats for the Value column
    try:
        # If Value is already numeric
        if pd.api.types.is_numeric_dtype(df['Value']):
            df['Value_Numeric'] = df['Value']
        else:
            # If Value is a string that needs to be converted
            df['Value_Numeric'] = df['Value'].astype(str).str.replace('$', '').str.replace(',', '').astype(float)
    except Exception as e:
        print(f"Error converting Value to numeric: {str(e)}")
        print(f"Value column sample: {df['Value'].head()}")
        # Create a fallback Value_Numeric column
        df['Value_Numeric'] = 0.0
    
    return df

# Page config
st.set_page_config(
    page_title="Fund of Funds Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with JavaScript for dynamic sizing
st.markdown(r"""
    <style>
    /* Base sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #0e1117;
        position: relative;
        border-right: 1px solid #2d3748 !important;
    }
    
    section[data-testid="stSidebar"] > div {
        background-color: #0e1117;
    }
    
    /* Chat messages container - position it directly above the input */
    .chat-messages-container {
        overflow-y: auto;
        max-height: calc(100vh - 200px); /* Increased from 160px to 200px to provide more space */
        margin-bottom: 140px !important; /* Add explicit bottom margin to create space for input */
        padding-bottom: 20px !important; /* Add padding at the bottom for extra spacing */
        display: flex;
        flex-direction: column;
    }
    
    /* Avatar styling */
    .avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background-size: cover;
        background-position: center;
        margin-right: 8px;
        margin-left: 8px;
        flex-shrink: 0;
    }
    
    .message-with-avatar {
        display: flex;
        align-items: flex-start;
        margin-bottom: 10px;
    }
    
    /* Target only the sidebar elements */
    /* Removed fixed positioning */
    
    /* Removed fixed positioning */
    
    /* Style textarea and button */
    section[data-testid="stSidebar"] .stTextArea {
        margin-bottom: 8px !important;
    }
    
    section[data-testid="stSidebar"] .stTextArea textarea {
        background-color: #2d3748 !important;
        color: white !important;
        border: 1px solid #4a5568 !important;
        border-radius: 10px !important;
        width: 100% !important;
        padding: 12px 15px !important;
        box-sizing: border-box !important;
    }
    
    /* Fix the outline effect to match the textarea */
    section[data-testid="stSidebar"] .stTextArea div[data-baseweb="textarea"] {
        width: 100% !important;
        border-radius: 10px !important;
        overflow: hidden !important;
    }
    
    section[data-testid="stSidebar"] .stButton button {
        background-color: #3b82f6 !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        width: 100% !important;
        padding: 10px !important;
        font-weight: 500 !important;
        font-size: 16px !important;
    }
    
    /* Add a solid background color to the bottom of the sidebar */
    .sidebar-bottom-bg {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 140px !important;
        background-color: #0e1117 !important;
        z-index: 998 !important;
        border-top: 1px solid #2d3748 !important;
    }
    
    /* Ticker mention dropdown styling */
    .ticker-dropdown {
        position: fixed;
        background-color: #1e293b;
        border: 1px solid #4a5568;
        border-radius: 5px;
        max-height: 200px;
        overflow-y: auto;
        z-index: 1001;
        width: 200px;
        display: none;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .ticker-item {
        padding: 8px 12px;
        cursor: pointer;
        color: white;
    }
    
    .ticker-item:hover {
        background-color: #2d3748;
    }
    
    .ticker-highlight {
        color: #3b82f6;
        font-weight: bold;
    }
    
    .fof-ticker {
        background-color: rgba(72, 187, 120, 0.1);
        border-left: 3px solid #48bb78;
    }
    
    .fof-badge {
        background-color: #48bb78;
        color: white;
        font-size: 0.7em;
        padding: 1px 4px;
        border-radius: 3px;
        margin-left: 5px;
        vertical-align: middle;
    }
    
    .ticker-dropdown-title {
        padding: 8px 12px;
        font-weight: bold;
        color: white;
        background-color: #2d3748;
        border-bottom: 1px solid #4a5568;
        text-align: center;
    }
    </style>
    
    <!-- Hidden element to store tickers data for JavaScript -->
    <div id="available-tickers" style="display: none;">{st.session_state.available_tickers}</div>
    <div id="fof-tickers" style="display: none;">{st.session_state.fof_tickers}</div>
    
    <div id="ticker-dropdown" class="ticker-dropdown"></div>
    
    <script>
    // Function to adjust input width based on sidebar width
    function adjustInputWidth() {
        const sidebar = document.querySelector('section[data-testid="stSidebar"]');
        if (!sidebar) return;
        
        const sidebarWidth = sidebar.offsetWidth;
        
        // Adjust textarea width
        const textareas = sidebar.querySelectorAll('textarea');
        textareas.forEach(textarea => {
            textarea.style.width = (sidebarWidth - 40) + 'px';
        });
        
        // Adjust button width
        const buttons = sidebar.querySelectorAll('button');
        buttons.forEach(button => {
            button.style.width = (sidebarWidth - 40) + 'px';
        });
        
        // Adjust bottom background width
        const bottomBg = document.querySelector('.sidebar-bottom-bg');
        if (bottomBg) {
            bottomBg.style.width = sidebarWidth + 'px';
        }
    }
    
    // Scroll to the bottom of the chat container
    function scrollToBottom() {
        const container = document.querySelector('.chat-messages-container');
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
    }
    
    // Adjust on load and resize
    window.addEventListener('load', () => {
        adjustInputWidth();
        scrollToBottom();
        setupTickerMentions();
    });
    
    window.addEventListener('resize', adjustInputWidth);
    
    // Scroll to the last message every time a new message is added
    const observer = new MutationObserver(scrollToBottom);
    
    // Start observing the chat container for changes
    setTimeout(() => {
        const container = document.querySelector('.chat-messages-container');
        if (container) {
            observer.observe(container, { childList: true, subtree: true });
        }
    }, 1000);
    
    // Ticker mention functionality
    function setupTickerMentions() {
        // Get available tickers from the server
        const availableTickers = JSON.parse(document.getElementById('available-tickers').textContent);
        const fofTickers = JSON.parse(document.getElementById('fof-tickers').textContent);
        
        // Find the textarea and create dropdown if it doesn't exist
        const textarea = document.querySelector('section[data-testid="stSidebar"] textarea');
        let dropdown = document.getElementById('ticker-dropdown');
        
        if (!dropdown) {
            dropdown = document.createElement('div');
            dropdown.id = 'ticker-dropdown';
            dropdown.className = 'ticker-dropdown';
            document.body.appendChild(dropdown);
        }
        
        if (!textarea) {
            // If textarea not found, try again after a delay
            setTimeout(setupTickerMentions, 1000);
            return;
        }
        
        let mentionActive = false;
        let mentionStart = 0;
        let currentQuery = '';
        
        // Add debug logging
        console.log('Ticker mention system initialized');
        console.log('Available tickers:', availableTickers.length);
        console.log('Fund-of-funds tickers:', fofTickers.length);
        
        textarea.addEventListener('input', (e) => {
            const text = textarea.value;
            const caretPos = textarea.selectionStart;
            
            console.log('Input detected, text:', text);
            
            // Check if we're in a potential @ mention situation
            let i = caretPos - 1;
            while (i >= 0 && text[i] !== '@' && text[i] !== ' ' && text[i] !== '\n') {
                i--;
            }
            
            if (i >= 0 && text[i] === '@') {
                console.log('@ detected at position', i);
                mentionActive = true;
                mentionStart = i;
                currentQuery = text.substring(i + 1, caretPos).toUpperCase();
                console.log('Current query:', currentQuery);
                
                // If the query is empty (just typed @), show all fund-of-funds first
                let filteredTickers = [];
                if (currentQuery === '') {
                    // Show all fund-of-funds first (up to 10)
                    filteredTickers = fofTickers.slice(0, 10);
                    console.log('Showing all FoFs:', filteredTickers);
                } else {
                    // Filter tickers based on current query
                    // Prioritize fund-of-funds that match the query
                    const matchingFoFs = fofTickers.filter(ticker => 
                        ticker.toUpperCase().includes(currentQuery)
                    );
                    
                    // Then add other tickers that match the query
                    const matchingOthers = availableTickers.filter(ticker => 
                        ticker.toUpperCase().includes(currentQuery) && !fofTickers.includes(ticker)
                    );
                    
                    // Combine with FoFs first, limit total to 10 results
                    filteredTickers = [...matchingFoFs, ...matchingOthers].slice(0, 10);
                    console.log('Filtered tickers:', filteredTickers);
                }
                
                if (filteredTickers.length > 0) {
                    console.log('Showing dropdown with', filteredTickers.length, 'items');
                    
                    // Position the dropdown - more robust positioning
                    const rect = textarea.getBoundingClientRect();
                    dropdown.style.position = 'fixed';
                    dropdown.style.left = rect.left + 'px';
                    dropdown.style.top = (rect.bottom + 5) + 'px'; // Position below the textarea
                    dropdown.style.zIndex = '9999'; // Ensure it's on top
                    
                    // Populate dropdown
                    dropdown.innerHTML = '';
                    dropdown.style.display = 'block'; // Explicitly set display to block
                    dropdown.style.width = '250px'; // Make it wider
                    dropdown.style.maxHeight = '300px'; // Make it taller
                    
                    // Add a title to the dropdown
                    const title = document.createElement('div');
                    title.className = 'ticker-dropdown-title';
                    title.textContent = currentQuery === '' ? 'Fund of Funds' : 'Matching Funds';
                    dropdown.appendChild(title);
                    
                    console.log('Dropdown positioned at', dropdown.style.left, dropdown.style.top);
                    filteredTickers.forEach(ticker => {
                        const item = document.createElement('div');
                        item.className = 'ticker-item';
                        
                        // Check if this is a fund-of-funds
                        const isFoF = fofTickers.includes(ticker);
                        if (isFoF) {
                            item.classList.add('fof-ticker');
                        }
                        
                        // Highlight the matching part
                        const index = ticker.toUpperCase().indexOf(currentQuery);
                        if (index !== -1) {
                            const before = ticker.substring(0, index);
                            const match = ticker.substring(index, index + currentQuery.length);
                            const after = ticker.substring(index + currentQuery.length);
                            
                            // Add a special indicator for fund-of-funds
                            const fofIndicator = isFoF ? ' <span class="fof-badge">FoF</span>' : '';
                            item.innerHTML = before + '<span class="ticker-highlight">' + match + '</span>' + after + fofIndicator;
                        } else {
                            // Add a special indicator for fund-of-funds
                            const fofIndicator = isFoF ? ' <span class="fof-badge">FoF</span>' : '';
                            item.innerHTML = ticker + fofIndicator;
                        }
                        
                        item.addEventListener('click', () => {
                            // Replace the @query with @ticker
                            const newText = text.substring(0, mentionStart) + '@' + ticker + ' ' + text.substring(caretPos);
                            textarea.value = newText;
                            
                            // Move caret position after the inserted ticker
                            const newCaretPos = mentionStart + ticker.length + 2; // +2 for @ and space
                            textarea.setSelectionRange(newCaretPos, newCaretPos);
                            
                            // Focus back on textarea
                            textarea.focus();
                            
                            // Hide dropdown
                            dropdown.style.display = 'none';
                            mentionActive = false;
                        });
                        
                        dropdown.appendChild(item);
                    });
                    
                    dropdown.style.display = 'block';
                } else {
                    dropdown.style.display = 'none';
                }
            } else {
                mentionActive = false;
                dropdown.style.display = 'none';
            }
        });
        
        // Hide dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (e.target !== dropdown && !dropdown.contains(e.target) && e.target !== textarea) {
                dropdown.style.display = 'none';
                mentionActive = false;
            }
        });
        
        // Handle keyboard navigation in dropdown
        textarea.addEventListener('keydown', (e) => {
            if (!mentionActive || dropdown.style.display === 'none') return;
            
            const items = dropdown.querySelectorAll('.ticker-item');
            let activeIndex = -1;
            
            // Find currently active item
            items.forEach((item, i) => {
                if (item.classList.contains('active')) {
                    activeIndex = i;
                }
            });
            
            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    if (activeIndex < items.length - 1) {
                        if (activeIndex >= 0) items[activeIndex].classList.remove('active');
                        items[activeIndex + 1].classList.add('active');
                    }
                    break;
                    
                case 'ArrowUp':
                    e.preventDefault();
                    if (activeIndex > 0) {
                        items[activeIndex].classList.remove('active');
                        items[activeIndex - 1].classList.add('active');
                    }
                    break;
                    
                case 'Enter':
                    e.preventDefault();
                    if (activeIndex >= 0) {
                        items[activeIndex].click();
                    } else if (items.length > 0) {
                        items[0].click();
                    }
                    break;
                    
                case 'Escape':
                    e.preventDefault();
                    dropdown.style.display = 'none';
                    mentionActive = false;
                    break;
            }
        });
    }
    </script>
""", unsafe_allow_html=True)

# Create a container for the top navigation that was previously in the sidebar
top_nav = st.container()

# Create a container for the main content
main_content = st.container()

# Left Panel - Chat Interface
with st.sidebar:
    # Initialize session state for chat messages if it doesn't exist
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Hello! I'm **BiL**, your Fund of Funds AI assistant. I can help answer questions about funds, investing strategies, and portfolio analysis. How can I assist you today?"}
        ]
    
    # Add a loading state for the chat
    if 'is_processing' not in st.session_state:
        st.session_state.is_processing = False
    
    # Function to handle sending a message
    def send_message():
        # Get the message from session state
        user_message = st.session_state.chat_input
        
        # Only process non-empty messages
        if user_message and user_message.strip():
            # Check if a ticker was selected from the dropdown
            if 'selected_ticker' in st.session_state and st.session_state.selected_ticker:
                # Replace @ticker_query with the selected ticker
                if '@ticker_query' in user_message:
                    user_message = user_message.replace('@ticker_query', f'@{st.session_state.selected_ticker}')
                    # Clear the selected ticker for next message
                    st.session_state.selected_ticker = None
            
            # Add user message to chat (only the original message, not the enhanced version)
            st.session_state.chat_messages.append({"role": "user", "content": user_message})
            
            # Set processing state to true
            st.session_state.is_processing = True
            
            # Get recent conversation history for context (last 10 messages)
            # We need to create a deep copy to avoid modifying the displayed messages
            recent_messages = []
            for msg in st.session_state.chat_messages[-10:] if len(st.session_state.chat_messages) > 10 else st.session_state.chat_messages:
                recent_messages.append(dict(msg))
            
            # Check for new tickers in the message
            potential_tickers = gemini_service.detect_tickers(user_message)
            if potential_tickers:
                # Add a temporary message indicating we're checking for fund data
                st.session_state.chat_messages.append({
                    "role": "assistant", 
                    "content": f"I see you've mentioned some fund tickers. Let me check if I have data for them...",
                    "is_temporary": True
                })
            
            # Check if @overlap is mentioned and if overlap data is available
            overlap_data = None
            if '@overlap' in user_message.lower() and 'overlap_data' in st.session_state and st.session_state.overlap_data:
                overlap_data = st.session_state.overlap_data
                st.session_state.chat_messages.append({
                    "role": "assistant", 
                    "content": f"I see you're asking about the current overlap analysis. Let me analyze that data for you...",
                    "is_temporary": True
                })
            
            # CRITICAL FIX: We need to make sure we're not modifying the displayed messages
            # The last message in recent_messages is the user's message that needs enhancement
            # We'll let GeminiService handle the enhancement internally and keep the original message in the UI
            
            # Get the actual response from Gemini
            response = gemini_service.get_response(recent_messages, session, overlap_data)
            
            # Remove any temporary messages
            st.session_state.chat_messages = [msg for msg in st.session_state.chat_messages if not msg.get("is_temporary")]
            
            # Add Gemini response to chat
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
            
            # Reset processing state
            st.session_state.is_processing = False
    
    # Function to handle @ mentions
    def handle_at_mention():
        # Get the current input text
        current_text = st.session_state.chat_input
        
        # Check if @ was just typed
        if current_text.endswith('@'):
            # Set a flag to show the ticker selector
            st.session_state.show_ticker_selector = True
            # Store the text before the @
            st.session_state.text_before_at = current_text[:-1]
            # Set placeholder for ticker query
            st.session_state.chat_input = current_text + 'ticker_query'
        else:
            # Check if we need to hide the ticker selector
            if 'show_ticker_selector' in st.session_state and st.session_state.show_ticker_selector:
                if '@ticker_query' not in current_text:
                    st.session_state.show_ticker_selector = False
    
    # Function to encode images to base64
    def get_base64_encoded_image(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    
    # Add the title
    st.markdown("<h1 class='chat-title'>Chat Assistant</h1>", unsafe_allow_html=True)
    
    # Create a container for the chat messages
    st.markdown('<div class="chat-messages-container">', unsafe_allow_html=True)
    
    # Default avatar images - using custom avatar images in a similar style
    user_avatar = "https://img.icons8.com/fluency/96/000000/user-male-circle.png"
    assistant_avatar = "https://img.icons8.com/?size=100&id=6nsw3h9gk8M8&format=png&color=000000"
    
    # Display all messages
    for i, message in enumerate(st.session_state.chat_messages):
        align = "flex-end" if message["role"] == "user" else "flex-start"
        bg_color = "#0e1117" if message["role"] == "user" else "#0e1117"
        text_color = "#ffffff" if message["role"] == "user" else "#ffffff"
        border_color = "#4a5568" if message["role"] == "user" else "#4a5568"
        avatar_url = user_avatar if message["role"] == "user" else assistant_avatar
        
        # Add a special class to the last message
        extra_class = " last-message" if i == len(st.session_state.chat_messages) - 1 else ""
        
        # For the assistant's first message, add special styling to BiL
        if i == 0 and message["role"] == "assistant":
            # Replace **BiL** with styled version
            content = message["content"].replace("**BiL**", "<span style='font-size: 1.2em; color: #4285F4; font-weight: bold;'>BiL</span>")
        else:
            # For other messages, escape HTML to prevent raw HTML from being displayed
            content = html.escape(message["content"])
        
        # Replace newlines with <br> tags for proper display
        content = content.replace('\n', '<br>')
        
        # For user messages, avatar comes after the message
        if message["role"] == "user":
            st.markdown(
                f"""
                <div style="display: flex; justify-content: {align}; margin-bottom: 10px;" class="message-with-avatar{extra_class}">
                    <div style="background-color: {bg_color}; color: {text_color}; padding: 10px; border-radius: 10px; max-width: 70%; word-wrap: break-word; border: 1px solid {border_color};">
                        {content}
                    </div>
                    <div class="avatar" style="background-image: url('{avatar_url}');"></div>
                </div>
                """, 
                unsafe_allow_html=True
            )
        # For assistant messages, avatar comes before the message
        else:
            st.markdown(
                f"""
                <div style="display: flex; justify-content: {align}; margin-bottom: 10px;" class="message-with-avatar{extra_class}">
                    <div class="avatar" style="background-image: url('{avatar_url}');"></div>
                    <div style="background-color: {bg_color}; color: {text_color}; padding: 10px; border-radius: 10px; max-width: 70%; word-wrap: break-word; border: 1px solid {border_color};">
                        {content}
                    </div>
                </div>
                """, 
                unsafe_allow_html=True
            )
    
    # Show a loading indicator when processing
    if st.session_state.is_processing:
        st.markdown(f"""
        <div class="chat-message" style="justify-content: flex-start;">
            <div class="avatar">
                <img src="{assistant_avatar}" style="width: 40px; height: 40px; border-radius: 50%;">
            </div>
            <div class="message" style="background-color: #0e1117; color: #ffffff; border: 1px solid #4a5568;">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Close the chat messages container
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Add a spacer div to ensure separation between messages and input
    st.markdown('<div style="height: 140px;"></div>', unsafe_allow_html=True)
    
    # Add a note about using Ctrl+Enter
    st.markdown("""
    <div style="text-align: center; color: #8e9aaf; font-size: 0.8em; margin-bottom: 10px;">
        Press Ctrl+Enter to send your message
    </div>
    """, unsafe_allow_html=True)
    
    # Add custom CSS
    st.markdown("""
    <style>
    .chat-title {
        text-align: center;
        margin-bottom: 20px;
    }
    
    .chat-messages-container {
        display: flex;
        flex-direction: column;
        gap: 10px;
        margin-bottom: 20px;
        max-height: 400px;
        overflow-y: auto;
        padding-right: 10px;
    }
    
    .chat-message {
        display: flex;
        align-items: flex-end;
        margin-bottom: 10px;
    }
    
    .avatar {
        margin-right: 8px;
        margin-left: 8px;
    }
    
    .message {
        padding: 10px;
        border-radius: 10px;
        max-width: 80%;
        word-wrap: break-word;
    }
    
    .chat-input-container {
        display: flex;
        gap: 10px;
    }
    
    .chat-input {
        flex-grow: 1;
    }
    
    /* Typing indicator animation */
    .typing-indicator {
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .typing-indicator span {
        height: 8px;
        width: 8px;
        background: #4a5568;
        border-radius: 50%;
        display: inline-block;
        margin: 0 3px;
        animation: typing 1.5s infinite ease-in-out;
    }
    
    .typing-indicator span:nth-child(1) {
        animation-delay: 0s;
    }
    
    .typing-indicator span:nth-child(2) {
        animation-delay: 0.3s;
    }
    
    .typing-indicator span:nth-child(3) {
        animation-delay: 0.6s;
    }
    
    @keyframes typing {
        0% {
            transform: translateY(0px);
            background: #4a5568;
        }
        28% {
            transform: translateY(-5px);
            background: #8e9aaf;
        }
        44% {
            transform: translateY(0px);
            background: #4a5568;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Add the input elements in the sidebar container
    with st.sidebar.container():
        # Initialize the message state if it doesn't exist
        if 'temp_message' not in st.session_state:
            st.session_state.temp_message = ""
        if 'show_fund_selector' not in st.session_state:
            st.session_state.show_fund_selector = False
            
        # Function to handle key events and update the message
        def handle_input_change():
            current_text = st.session_state.chat_input
            st.session_state.temp_message = current_text
            
            # Check if @ was typed
            if '@' in current_text and not st.session_state.show_fund_selector:
                # Show the fund selector
                st.session_state.show_fund_selector = True
            
            # If the @ was removed, hide the fund selector
            if '@' not in current_text and st.session_state.show_fund_selector:
                st.session_state.show_fund_selector = False
            
        # Function to handle fund selection
        def select_fund(fund_ticker):
            # Get the current message
            current_text = st.session_state.temp_message
            # Replace the @ with the selected fund
            if '@' in current_text:
                # Find the position of @ and replace it with @fund_ticker
                at_pos = current_text.rfind('@')
                new_text = current_text[:at_pos] + f'@{fund_ticker} ' + current_text[at_pos+1:].lstrip()
                st.session_state.chat_input = new_text
                st.session_state.temp_message = new_text
            # Hide the fund selector
            st.session_state.show_fund_selector = False
            
        # Function to send the message when the button is clicked
        def handle_send_click():
            if st.session_state.temp_message.strip():
                # Store the message in a temporary variable
                message_to_send = st.session_state.temp_message
                # Clear the input field
                st.session_state.chat_input = ""
                st.session_state.temp_message = ""
                # Update the chat_input in session state to trigger the message sending
                st.session_state.chat_input = message_to_send
                # Call send_message
                send_message()
                # Clear the input again
                st.session_state.chat_input = ""
                # Hide the fund selector
                st.session_state.show_fund_selector = False
        
        # Text area for input
        user_input = st.text_area(
            "Type your message", 
            height=70, 
            placeholder="Type your message (Use @ to mention a fund, Press Ctrl+Enter to send)", 
            label_visibility="collapsed", 
            key="chat_input",
            on_change=handle_input_change
        )
        
        # Show fund selector if needed
        if st.session_state.show_fund_selector:
            st.markdown("### Select a Fund")
            
            # Get fund-of-funds tickers
            fof_tickers = FundService.get_fund_of_funds_tickers(session)
            
            # Show fund-of-funds with a special indicator
            st.markdown("**Fund of Funds**")
            cols = st.columns(2)
            for i, ticker in enumerate(fof_tickers[:10]):
                col_idx = i % 2
                with cols[col_idx]:
                    if st.button(f"{ticker} 🔄", key=f"fof_{ticker}", use_container_width=True):
                        select_fund(ticker)
            
            # Show other funds if there's space
            if len(fof_tickers) < 10:
                st.markdown("**Other Funds**")
                all_tickers = FundService.get_all_fund_tickers(session)
                other_tickers = [t for t in all_tickers if t not in fof_tickers]
                
                cols = st.columns(2)
                for i, ticker in enumerate(other_tickers[:(10-len(fof_tickers))]):
                    col_idx = i % 2
                    with cols[col_idx]:
                        if st.button(ticker, key=f"other_{ticker}", use_container_width=True):
                            select_fund(ticker)
        
        # Add JavaScript to capture Ctrl+Enter
        st.markdown("""
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Function to find the textarea and button
            function setupCtrlEnter() {
                const textarea = document.querySelector('section[data-testid="stSidebar"] textarea');
                const button = document.querySelector('section[data-testid="stSidebar"] button');
                
                if (!textarea || !button) {
                    setTimeout(setupCtrlEnter, 500);
                    return;
                }
                
                // Add the event listener
                textarea.addEventListener('keydown', function(e) {
                    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                        e.preventDefault();
                        button.click();
                    }
                });
            }
            
            setupCtrlEnter();
        });
        </script>
        """, unsafe_allow_html=True)
        
        # Button to send the message
        if st.button("Send", use_container_width=True, on_click=handle_send_click):
            pass

# Top Navigation (moved from sidebar)
with top_nav:
    # Create a complete HTML structure for the top navigation
    html_content = """
    <div class="top-nav">
        <div class="top-nav-item" id="view-selection-container">
            <!-- View selection will be inserted by Streamlit -->
        </div>
        <div class="top-nav-item" id="search-type-container">
            <!-- Search type selection will be inserted by Streamlit -->
        </div>
        <div class="top-nav-item" id="search-input-container">
            <!-- Search input will be inserted by Streamlit -->
        </div>
        <div class="top-nav-item" id="search-button-container">
            <!-- Search button will be inserted by Streamlit -->
        </div>
    </div>
    """
    st.markdown(html_content, unsafe_allow_html=True)
    
    # Insert Streamlit elements into the placeholders
    with st.container():
        # Override the default container styling to position it in our custom container
        st.markdown("""
            <style>
            #view-selection-container > .element-container {
                margin-bottom: 0 !important;
            }
            </style>
        """, unsafe_allow_html=True)
        # Default to Portfolio Analysis (index 1)
        selected_view = st.radio(
            "Select View",
            ["Individual Fund Structure", "Portfolio Analysis"],
            index=1,  # Always default to Portfolio Analysis
            key="view_selection",
            label_visibility="collapsed"
        )
    
    if selected_view == "Individual Fund Structure":
        with st.container():
            # Override the default container styling
            st.markdown("""
                <style>
                #search-type-container > .element-container {
                    margin-bottom: 0 !important;
                }
                </style>
            """, unsafe_allow_html=True)
            search_type = st.radio("Search by:", ["Ticker", "CUSIP"], key="search_type", label_visibility="collapsed")
        
        with st.container():
            # Override the default container styling
            st.markdown("""
                <style>
                #search-input-container > .element-container {
                    margin-bottom: 0 !important;
                }
                </style>
            """, unsafe_allow_html=True)
            if search_type == "Ticker":
                search_input = st.text_input(
                    "Enter Fund Ticker:",
                    placeholder="i.e. MDIZX",
                    help="Enter a fund ticker symbol (e.g., MDIZX)",
                    key="search_input",
                    label_visibility="collapsed"
                )
            else:
                search_input = st.text_input(
                    "Enter CUSIP:",
                    placeholder="Enter 9-digit CUSIP",
                    help="Enter a valid 9-digit CUSIP number",
                    key="search_input_cusip",
                    label_visibility="collapsed"
                )
        
        with st.container():
            # Override the default container styling
            st.markdown("""
                <style>
                #search-button-container > .element-container {
                    margin-bottom: 0 !important;
                }
                </style>
            """, unsafe_allow_html=True)
            search_button = st.button("🔍 Search", key="search_button")

# Main content area
with main_content:
    if selected_view == "Individual Fund Structure":
        # Main content area for individual fund
        if search_button and search_input:
            # Get fund data
            fund = FundService.get_fund_by_ticker(session, search_input) if search_type == "Ticker" else None
            # TODO: Implement CUSIP search
            
            if fund:
                # Get query parameters to determine active tab
                params = st.query_params
                active_tab = 0  # Default to first tab
                
                # Check if we have an active tab in the URL
                if "tab" in params:
                    try:
                        tab_index = int(params["tab"])
                        if 0 <= tab_index <= 4:  # We have 5 tabs (0-4)
                            active_tab = tab_index
                    except ValueError:
                        pass
                
                # Create tabs for the fund details
                tab_names = [
                    "Fund Overview",
                    "Portfolio",
                    "Securities Analysis",
                    "Institutional Holdings",
                    "Investor Information"
                ]
                
                tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_names)
                
                # Fund Overview Tab
                with tab1:
                    # Set query parameter for this tab
                    st.query_params["tab"] = "0"
                    st.header(f"{fund.ticker} - {fund.name}")
                    
                    # Summary metrics
                    st.subheader("Summary Metrics")
                    holdings = FundService.get_holdings_details(session, fund.ticker)
                    
                    # Debug output
                    print(f"\nHoldings columns for {fund.ticker}: {holdings.columns.tolist()}")
                    if not holdings.empty:
                        print(f"Sample Value: {holdings['Value'].iloc[0] if 'Value' in holdings.columns else 'N/A'}")
                    
                    # Apply data transformations
                    holdings = prepare_holdings_data(holdings)
                    
                    # Calculate total value safely
                    if 'Value_Numeric' in holdings.columns and not holdings.empty:
                        total_value = holdings['Value_Numeric'].sum()
                    else:
                        # Fallback: Try to calculate from the Value column directly
                        try:
                            if 'Value' in holdings.columns:
                                # Convert Value column on the fly
                                total_value = holdings['Value'].astype(str).str.replace('$', '').str.replace(',', '').astype(float).sum()
                            else:
                                # Use the total_assets from the filing
                                total_value = fund.filings[0].total_assets if fund.filings else 0.0
                        except Exception as e:
                            print(f"Error calculating total value: {str(e)}")
                            total_value = 0.0
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Assets", f"${total_value:,.2f}")
                    with col2:
                        st.metric("Direct Holdings", len(holdings))
                    with col3:
                        st.metric("Filing Date", fund.filings[0].filing_date.strftime("%Y-%m-%d") if fund.filings else "N/A")
                    
                    # Asset allocation
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Asset Allocation")
                        
                        # Check if Category column exists
                        if 'Category' in holdings.columns and not holdings.empty:
                            try:
                                fig = px.pie(
                                    holdings,
                                    values='Value_Numeric',  # Use Value_Numeric
                                    names='Category',
                                    title="By Category"
                                )
                                st.plotly_chart(fig)
                            except Exception as e:
                                st.warning(f"Could not create asset allocation chart: {str(e)}")
                                st.info("Asset allocation data not available for this fund.")
                        else:
                            # Create a default chart or show a message
                            st.info("Asset allocation data not available for this fund.")
                            
                            # If we have any columns that could be used for categorization
                            if len(holdings.columns) > 0 and not holdings.empty:
                                st.write("Available data columns:")
                                st.write(", ".join(holdings.columns.tolist()))
                    
                    with col2:
                        st.subheader("Direct Holdings")
                        
                        # Check if holdings data exists and has the necessary columns
                        if not holdings.empty and 'Value_Numeric' in holdings.columns:
                            try:
                                # Sort first, then select display columns
                                sorted_holdings = holdings.sort_values('Value_Numeric', ascending=False)
                                
                                # Determine which columns to display based on what's available
                                display_cols = []
                                for col in ['Name', 'Value', 'Pct', 'Category']:
                                    if col in sorted_holdings.columns:
                                        display_cols.append(col)
                                
                                if display_cols:
                                    st.dataframe(sorted_holdings[display_cols])
                                else:
                                    st.info("No holdings data available to display.")
                            except Exception as e:
                                st.warning(f"Error displaying holdings: {str(e)}")
                                st.info("Could not display holdings data in the expected format.")
                        else:
                            st.info("No holdings data available for this fund.")
            
                # Underlying Funds Tab
                with tab2:
                    # Set query parameter for this tab
                    st.query_params["tab"] = "1"
                    st.header("Fund Structure")
                    try:
                        render_fund_structure(session, fund.ticker)
                    except Exception as e:
                        st.warning(f"Error rendering fund structure: {str(e)}")
                        st.info("Fund structure data not available for this fund.")
            
                # Securities Analysis Tab
                with tab3:
                    # Set query parameter for this tab
                    st.query_params["tab"] = "2"
                    st.header("Securities Analysis")
                    
                    # Create a single tab for underlying securities
                    sec_tab1 = st.tabs(["Underlying Securities"])[0]
                    
                    with sec_tab1:
                        # Aggregate holdings across all underlying funds
                        all_securities = []
                        
                        # Check if holdings data exists and has the necessary columns
                        if not holdings.empty and 'Ticker' in holdings.columns:
                            try:
                                for _, holding in holdings.iterrows():
                                    ticker_value = holding.get('Ticker')
                                    if ticker_value and str(ticker_value).upper() != 'NONE':
                                        underlying = FundService.get_holdings_details(session, ticker_value)
                                        if not underlying.empty:
                                            underlying = prepare_holdings_data(underlying)
                                            all_securities.extend(underlying.to_dict('records'))
                            except Exception as e:
                                st.warning(f"Error processing underlying holdings: {str(e)}")
                        else:
                            st.info("No holdings data available to analyze underlying securities.")
                        
                        if all_securities:
                            securities_df = pd.DataFrame(all_securities)
                            securities_df = prepare_holdings_data(securities_df)
                            
                            # Top securities by value - sort first, then select columns for display
                            st.subheader("Top Securities")
                            top_20 = securities_df.nlargest(20, 'Value_Numeric')
                            
                            fig = px.bar(
                                top_20,
                                x='Name',
                                y='Value_Numeric',
                                title="Top 20 Securities by Value",
                                labels={'Value_Numeric': 'Value ($)'}
                            )
                            fig.update_layout(xaxis_tickangle=-45)
                            st.plotly_chart(fig)
                            
                            # Securities table - sort first, then select display columns
                            sorted_securities = securities_df.sort_values('Value_Numeric', ascending=False)
                            st.dataframe(
                                sorted_securities[['Name', 'Value', 'Pct', 'Category']].head(50)
                            )
                    

            
                # Institutional Holdings Tab - Now at the top level
                with tab4:
                    # Set query parameter for this tab
                    st.query_params["tab"] = "3"
                    st.header("Institutional Holdings Comparison")
                    
                    # Create a key for institutional holdings state
                    inst_key = f"inst_holdings_state_{fund.ticker}"
                    
                    # Initialize state if needed
                    if inst_key not in st.session_state:
                        st.session_state[inst_key] = {
                            "selected_institution": None,
                            "institutions": None
                        }
                    
                    # Get all institutions first - do this outside the component
                    if not st.session_state[inst_key]["institutions"]:
                        institutions = InstitutionalService.get_all_institutions(session)
                        st.session_state[inst_key]["institutions"] = institutions
                        if institutions:
                            st.session_state[inst_key]["selected_institution"] = institutions[0]["id"]
                    
                    # Get institutions from state
                    institutions = st.session_state[inst_key]["institutions"]
                    
                    # Create tabs for each institution
                    if institutions:
                        institution_options = {inst['name']: inst['id'] for inst in institutions}
                        institution_names = list(institution_options.keys())
                        
                        # No refresh button needed
                        refresh = False
                        
                        # Create tabs for each institution
                        inst_tabs = st.tabs(institution_names)
                        
                        # Preload all data for better user experience
                        if "inst_data_cache" not in st.session_state:
                            st.session_state["inst_data_cache"] = {}
                            
                        # Render each institution in its own tab
                        for i, (name, tab) in enumerate(zip(institution_names, inst_tabs)):
                            with tab:
                                institution_id = institution_options[name]
                                
                                # Create a unique key for this institution's data
                                cache_key = f"{fund.ticker}_{institution_id}"
                                
                                # Check if we need to refresh or if data isn't cached
                                if refresh or cache_key not in st.session_state["inst_data_cache"]:
                                    # Render the component with the selected institution
                                    render_institutional_holdings_analysis(
                                        session, 
                                        fund.ticker, 
                                        institution_id,
                                        force_refresh=refresh
                                    )
                                    
                                    # Cache the rendered component
                                    st.session_state["inst_data_cache"][cache_key] = True
                                else:
                                    # Render from cache
                                    render_institutional_holdings_analysis(
                                        session, 
                                        fund.ticker, 
                                        institution_id,
                                        force_refresh=False
                                    )
                    else:
                        st.warning("No institutional investors found in the database.")
                
                # Investor Information Tab
                with tab5:
                    # Set query parameter for this tab
                    st.query_params["tab"] = "4"
                    st.header("Investor Information")
                    
                    if fund.filings:
                        latest_filing = fund.filings[0]
                        
                        # Historical metrics
                        st.subheader("Historical Data")
                        st.info("Historical performance metrics coming soon")
                        
                        # Fund details
                        st.subheader("Fund Details")
                        st.write(f"**Fund Type:** {fund.fund_type}")
                        st.write(f"**Latest Filing Date:** {latest_filing.filing_date}")
                        st.write(f"**Total Assets:** ${latest_filing.total_assets:,.2f}")
                    else:
                        st.warning("No filing data available")
        
        else:
            st.error(f"No fund found with {search_type}: {search_input}")

    else:  # Portfolio Analysis View
        st.title("Portfolio Analysis")
        
        try:
            # Get all funds with their types
            funds = FundService.get_all_mutual_funds(session)
            
            # Create two columns for fund selection
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📦 Fund of Funds")
                fof_options = [
                    f['ticker'] 
                    for f in funds 
                    if FundService.get_fund_by_ticker(session, f['ticker']).fund_type == 'fund_of_funds'
                ]
                selected_fofs = st.multiselect(
                    "Select Fund of Funds",
                    options=fof_options,
                    default=["MDIZX"] if "MDIZX" in fof_options else [],  # Default to MDIZX if available
                    help="Select the main funds you want to analyze",
                    key="selected_fofs"
                )
            
            with col2:
                st.subheader("📈 Fund Holdings")
                # Get holdings of selected FoFs
                holdings_options = []
                if selected_fofs:
                    for fof in selected_fofs:
                        holdings = FundService.get_fund_holdings(session, fof)
                        holdings_options.extend([
                            {
                                'value': h.ticker if h.ticker and h.ticker != 'None' else h.name,
                                'label': f"{h.name} ({h.ticker})" if h.ticker and h.ticker != 'None' else h.name,
                                'is_ticker': bool(h.ticker and h.ticker != 'None')
                            }
                            for h in holdings 
                            if h.ticker or h.name
                        ])
                    # Remove duplicates based on value
                    holdings_options = list({opt['value']: opt for opt in holdings_options}.values())
            
                # Get default holdings for MDIZX if it's selected
                default_holdings = []
                if 'MDIZX' in selected_fofs:
                    # Get MDIZX holdings
                    mdizx_holdings = FundService.get_fund_holdings(session, 'MDIZX')
                    # Create labels for the holdings that match the format in holdings_options
                    for h in mdizx_holdings:
                        if h.ticker and h.ticker != 'None':
                            default_holdings.append(f"{h.name} ({h.ticker})")
                        else:
                            default_holdings.append(h.name)
                    # Filter to only include options that exist in holdings_options
                    available_labels = [opt['label'] for opt in holdings_options]
                    default_holdings = [h for h in default_holdings if h in available_labels]
                
                selected_holdings = st.multiselect(
                    "Select Holdings to Include",
                    options=[opt['label'] for opt in holdings_options],  # Show labels in dropdown
                    default=default_holdings,
                    help="Select underlying funds to include in the analysis"
                )
                
                # Map selected labels back to values for analysis
                selected_values = [
                    next(opt['value'] for opt in holdings_options if opt['label'] == label)
                    for label in selected_holdings
                ]
                
                # Combine selections for analysis
                selected_funds = selected_fofs + selected_values
        
            if selected_funds:
                render_portfolio_analysis(session, selected_funds)
            else:
                st.info("Please select at least one Fund of Funds to analyze")
                
        except Exception as e:
            st.error(f"Error loading funds: {str(e)}")
            st.code(traceback.format_exc())

# Clean up
session.close()