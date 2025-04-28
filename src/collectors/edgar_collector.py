import pandas as pd
import requests
import time
from edgar import *
from typing import List, Dict, Optional
from src.utils.logger import setup_logger
from dotenv import load_dotenv
import os

class EdgarCollector:
    """Collector for retrieving NPORT filings and fund holdings data."""
    
    def __init__(self):
        load_dotenv()
        self._initialize_credentials()
        self.logger = setup_logger('edgar_collector')
    
    def _initialize_credentials(self) -> None:
        """Initialize SEC and OpenFIGI credentials."""
        self.sec_identity = os.getenv('SEC_USER_AGENT')
        if not self.sec_identity:
            raise ValueError("SEC_USER_AGENT not found in environment variables")
            
        self.openfigi_api_key = os.getenv('OPENFIGI_API_KEY')
        if not self.openfigi_api_key:
            raise ValueError("OPENFIGI_API_KEY not found in environment variables")
            
        # Set SEC identity
        set_identity(self.sec_identity)

    def cusip_to_ticker(self, cusip_list: List[str]) -> Dict[str, str]:
        """Convert CUSIP numbers to ticker symbols using OpenFIGI API.
        
        Respects OpenFIGI API rate limits:
        - Up to 25,000 jobs per minute for bulk mapping
        - Maximum of 250 combined jobs per minute per API key
        
        Args:
            cusip_list: List of CUSIP identifiers to convert to tickers
            
        Returns:
            Dictionary mapping CUSIPs to their corresponding tickers
        """
        url = "https://api.openfigi.com/v3/mapping"
        headers = {
            "Content-Type": "application/json",
            "X-OPENFIGI-APIKEY": self.openfigi_api_key
        }
        
        # Remove duplicates to minimize API calls
        unique_cusips = list(set([c for c in cusip_list if c and str(c).upper() != 'NONE']))
        self.logger.info(f"Processing {len(unique_cusips)} unique CUSIPs")
        
        # Initialize results dictionary
        results = {}
        
        # Process in chunks of 100 to avoid hitting API limits
        # OpenFIGI allows up to 100 items per request
        chunk_size = 100
        chunks = [unique_cusips[i:i + chunk_size] for i in range(0, len(unique_cusips), chunk_size)]
        
        self.logger.info(f"Split into {len(chunks)} chunks of up to {chunk_size} CUSIPs each")
        
        # Track requests to stay within rate limits
        request_count = 0
        max_requests_per_minute = 250  # OpenFIGI combined limit
        
        for i, chunk in enumerate(chunks):
            # Check if we're approaching rate limits
            if request_count >= max_requests_per_minute:
                self.logger.warning(f"Approaching rate limit ({request_count} requests). Pausing for 60 seconds.")
                time.sleep(60)  # Wait for a minute before continuing
                request_count = 0  # Reset counter
            
            payload = [{"idType": "ID_CUSIP", "idValue": cusip} for cusip in chunk]
            
            try:
                self.logger.info(f"Processing chunk {i+1}/{len(chunks)} with {len(chunk)} CUSIPs")
                response = requests.post(url, json=payload, headers=headers)
                request_count += 1
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for j, item in enumerate(data):
                        if item and "data" in item and item["data"]:
                            results[chunk[j]] = item["data"][0].get("ticker", "Not Found")
                        else:
                            results[chunk[j]] = "Not Found"
                            
                elif response.status_code == 429 or response.status_code == 413:  # Too Many Requests or Payload Too Large
                    self.logger.warning(f"Rate limit hit (status {response.status_code}). Pausing for 60 seconds.")
                    time.sleep(60)  # Wait for a minute before retrying
                    
                    # Retry with smaller chunks if we got a 413 error
                    if response.status_code == 413 and len(chunk) > 10:
                        self.logger.info(f"Retrying with smaller chunks")
                        smaller_chunks = [chunk[k:k + 10] for k in range(0, len(chunk), 10)]
                        
                        for small_chunk in smaller_chunks:
                            small_payload = [{"idType": "ID_CUSIP", "idValue": cusip} for cusip in small_chunk]
                            retry_response = requests.post(url, json=small_payload, headers=headers)
                            request_count += 1
                            
                            if retry_response.status_code == 200:
                                retry_data = retry_response.json()
                                for k, retry_item in enumerate(retry_data):
                                    if retry_item and "data" in retry_item and retry_item["data"]:
                                        results[small_chunk[k]] = retry_item["data"][0].get("ticker", "Not Found")
                                    else:
                                        results[small_chunk[k]] = "Not Found"
                            else:
                                # If even smaller chunks fail, mark as not found
                                for cusip in small_chunk:
                                    results[cusip] = "Not Found"
                            
                            # Small delay between requests
                            time.sleep(0.5)
                    else:
                        # Mark all CUSIPs in this chunk as not found
                        for cusip in chunk:
                            results[cusip] = "Not Found"
                else:
                    self.logger.error(f"OpenFIGI API error: {response.status_code} - {response.text}")
                    # Mark all CUSIPs in this chunk as not found
                    for cusip in chunk:
                        results[cusip] = "Not Found"
                
                # Small delay between chunks to avoid hitting rate limits
                if i < len(chunks) - 1:  # No need to sleep after the last chunk
                    time.sleep(0.5)
                    
            except Exception as e:
                self.logger.error(f"Error processing chunk {i+1}: {str(e)}")
                # Mark all CUSIPs in this chunk as not found
                for cusip in chunk:
                    results[cusip] = "Not Found"
        
        # Make sure all original CUSIPs are in the results
        final_results = {}
        for cusip in cusip_list:
            if cusip and str(cusip).upper() != 'NONE':
                final_results[cusip] = results.get(cusip, "Not Found")
            else:
                final_results[cusip] = "Not Found"
                
        self.logger.info(f"CUSIP to ticker mapping complete. Found tickers for {sum(1 for v in final_results.values() if v != 'Not Found')}/{len(cusip_list)} CUSIPs")
        return final_results

    def retrieve_nport_filings(self, tickers: List[str]) -> List[str]:
        """Retrieve NPORT filings for a list of tickers.
        
        This method attempts to find NPORT-P filings for each ticker. For mutual funds,
        it will retrieve and save the holdings data. For non-mutual fund securities
        (like stocks and ETFs), it will gracefully skip them since they don't file NPORT-P reports.
        
        Args:
            tickers: List of ticker symbols to process
            
        Returns:
            List of underlying ticker symbols found in the NPORT filings
        """
        import os
        
        # Filter out tickers with invalid characters
        filtered_tickers = []
        for ticker in tickers:
            if ticker and isinstance(ticker, str):
                # Skip tickers with spaces or special characters
                if ' ' in ticker or '/' in ticker or '\\' in ticker or len(ticker) < 2:
                    self.logger.info(f"Skipping ticker with invalid characters: {ticker}")
                    continue
                
                # Include all valid tickers
                filtered_tickers.append(ticker)
        
        self.logger.info(f"Processing {len(filtered_tickers)} potential tickers with NPORT filings")
        
        # Check for existing CSV files first
        tickers_to_process = []
        for ticker in filtered_tickers:
            csv_path = f"{ticker}.csv"
            if os.path.exists(csv_path):
                print(f"DEBUG: CSV file already exists for {ticker}, skipping retrieval")
                self.logger.info(f"CSV file already exists for {ticker}, skipping retrieval")
            else:
                print(f"DEBUG: CSV file does not exist for {ticker}, will process")
                tickers_to_process.append(ticker)
                
        self.logger.info(f"Will retrieve NPORT filings for {len(tickers_to_process)} tickers")
        
        # Add a delay between each API call to respect SEC EDGAR rate limits
        # SEC recommends no more than 10 requests per second, but we'll be more conservative
        api_delay = 10  # seconds between API calls
        max_retries = 3  # maximum number of retries for each ticker
        
        successful_tickers = []
        failed_tickers = []
        
        # Process each ticker
        for ticker in tickers_to_process:
            retry_count = 0
            success = False
            
            # Try up to max_retries times
            while retry_count < max_retries and not success:
                if retry_count > 0:
                    print(f"DEBUG: Retry #{retry_count} for {ticker}")
                    self.logger.info(f"Retry #{retry_count} for {ticker}")
                    # Exponential backoff for retries
                    time.sleep(api_delay * (2 ** retry_count))
                
                try:
                    print(f"DEBUG: Attempting to retrieve NPORT filings for {ticker}")
                    
                    # First check if this is a mutual fund
                    company_result = find(ticker)
                    
                    # Handle case where find returns None
                    if company_result is None:
                        print(f"DEBUG: No company found for ticker {ticker}")
                        self.logger.warning(f"No company found for ticker {ticker}")
                        break  # No point in retrying if company doesn't exist
                    
                    # Handle case where find returns CompanySearchResults (multiple matches)
                    if not hasattr(company_result, 'filings'):
                        print(f"DEBUG: Multiple companies found for ticker {ticker}, cannot determine which is correct")
                        self.logger.warning(f"Multiple companies found for ticker {ticker}, cannot determine which is correct")
                        break  # No point in retrying if we can't determine the correct company
                    
                    print(f"DEBUG: Found company for {ticker}")
                    
                    # Try to get NPORT-P filings
                    filings = company_result.filings.filter(form="NPORT-P")
                    
                    # Check if we found any filings
                    if not filings or len(filings) == 0:
                        print(f"DEBUG: No NPORT-P filings found for {ticker}")
                        self.logger.warning(f"No NPORT-P filings found for {ticker}")
                        break  # No point in retrying if no filings exist
                    
                    print(f"DEBUG: Found {len(filings)} NPORT-P filings for {ticker}")
                    
                    # Get the investments table from the first filing
                    investments_table = filings[0].obj().investments_table
                    print(f"DEBUG: Retrieved investments table for {ticker}")
                    
                    # Add delay after successful API call to respect rate limits
                    time.sleep(api_delay)
                    
                    # Extract column headers
                    columns = [column.header for column in investments_table.columns]
                    print(f"DEBUG: Extracted column headers: {columns}")
                    
                    # Extract column data and create rows
                    rows = list(zip(*[column._cells for column in investments_table.columns]))
                    print(f"DEBUG: Extracted {len(rows)} rows of data")
                    
                    # Convert to DataFrame
                    df = pd.DataFrame(rows, columns=columns)
                    print(f"DEBUG: Created DataFrame with shape {df.shape}")
                    
                    # Clean Value and Pct columns
                    if 'Value' in df.columns:
                        df['Value'] = (df['Value'].astype(str)
                                     .str.replace("$", "", regex=False)
                                     .str.replace(",", "", regex=False))
                        df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
                    
                    if 'Pct' in df.columns:
                        df['Pct'] = pd.to_numeric(df['Pct'], errors='coerce')
                    
                    # Save to CSV
                    csv_filename = f"{ticker}.csv"
                    df.to_csv(csv_filename, index=False)
                    print(f"DEBUG: Data written to {csv_filename}")
                    self.logger.info(f"Data written to {csv_filename}")
                    
                    # Mark as successful and add to successful tickers list
                    success = True
                    successful_tickers.append(ticker)
                    
                except Exception as e:
                    print(f"DEBUG ERROR: Error processing {ticker}: {str(e)}")
                    self.logger.error(f"Error processing {ticker}: {str(e)}")
                    import traceback
                    print(f"DEBUG TRACEBACK: {traceback.format_exc()}")
                    retry_count += 1
            
            # If we've exhausted all retries and still failed, add to failed_tickers
            if not success and retry_count >= max_retries:
                failed_tickers.append(ticker)
                self.logger.warning(f"Failed to process {ticker} after {max_retries} retries")
        
        # Add tickers from existing CSV files to successful_tickers
        for ticker in filtered_tickers:
            if ticker not in successful_tickers and ticker not in failed_tickers:
                csv_path = f"{ticker}.csv"
                if os.path.exists(csv_path):
                    successful_tickers.append(ticker)
        
        # Log summary
        self.logger.info(f"Successfully processed {len(successful_tickers)} tickers: {successful_tickers}")
        if failed_tickers:
            self.logger.warning(f"Failed to process {len(failed_tickers)} tickers: {failed_tickers}")
            
        # Process underlying securities - map CUSIPs to tickers but don't retrieve their NPORT filings
        # We'll only return tickers from successful retrievals
        all_underlying_tickers = []
        for ticker in successful_tickers:
            csv_path = f"{ticker}.csv"
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                if 'Cusip' in df.columns:
                    # Map CUSIPs to tickers and update the database
                    cusip_map = self.cusip_to_ticker(df['Cusip'].tolist())
                    self.logger.info(f"Mapped {len([t for t in cusip_map.values() if t != 'Not Found'])} CUSIPs to tickers for {ticker}")
                    
                    # Add to the list of underlying tickers
                    underlying_tickers = [t for t, c in zip(df['Ticker'].tolist(), df['Cusip'].tolist()) 
                                         if not pd.isna(t) and t != '']
                    all_underlying_tickers.extend(underlying_tickers)
        
        return all_underlying_tickers