import pandas as pd
import requests
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
        """Convert CUSIP numbers to ticker symbols using OpenFIGI API."""
        url = "https://api.openfigi.com/v3/mapping"
        headers = {
            "Content-Type": "application/json",
            "X-OPENFIGI-APIKEY": self.openfigi_api_key
        }
        
        payload = [{"idType": "ID_CUSIP", "idValue": cusip} for cusip in cusip_list]
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                self.logger.debug(f"OpenFIGI Response: {data}")
                
                results = {}
                for i, item in enumerate(data):
                    if item and "data" in item and item["data"]:
                        results[cusip_list[i]] = item["data"][0].get("ticker", "Not Found")
                    else:
                        results[cusip_list[i]] = "Not Found"
                return results
            else:
                self.logger.error(f"OpenFIGI API error: {response.status_code}")
                return {cusip: "Not Found" for cusip in cusip_list}
        except Exception as e:
            self.logger.error(f"Error in cusip_to_ticker: {str(e)}")
            return {cusip: "Not Found" for cusip in cusip_list}

    def retrieve_nport_filings(self, tickers: List[str]) -> None:
        """Retrieve NPORT filings for a list of tickers."""
        for ticker in tickers:
            try:
                print(f"DEBUG: Attempting to retrieve NPORT filings for {ticker}")
                # Get NPORT filing
                try:
                    company = find(ticker)
                    print(f"DEBUG: Found company for {ticker}")
                    
                    filings = company.filings.filter(form="NPORT-P")
                    print(f"DEBUG: Found {len(filings)} NPORT-P filings for {ticker}")
                    
                    if len(filings) == 0:
                        print(f"DEBUG: No NPORT-P filings found for {ticker}")
                        self.logger.warning(f"No NPORT-P filings found for {ticker}")
                        continue
                    
                    investments_table = filings[0].obj().investments_table
                    print(f"DEBUG: Retrieved investments table for {ticker}")
                except Exception as e:
                    print(f"DEBUG ERROR: Error finding NPORT filings for {ticker}: {str(e)}")
                    self.logger.error(f"Error finding NPORT filings for {ticker}: {str(e)}")
                    import traceback
                    print(f"DEBUG TRACEBACK: {traceback.format_exc()}")
                    continue
                
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
                
                # Process underlying fund holdings
                if 'Cusip' in df.columns:
                    cusip_map = self.cusip_to_ticker(df['Cusip'].tolist())
                    fof_tickers = [t for t in cusip_map.values() if t != "Not Found"]
                    
                    for underlying_ticker in fof_tickers:
                        try:
                            # Get underlying fund data
                            underlying_table = find(underlying_ticker).filings.filter(form="NPORT-P")[0].obj().investments_table
                            
                            # Process underlying data
                            underlying_columns = [column.header for column in underlying_table.columns]
                            underlying_rows = list(zip(*[column._cells for column in underlying_table.columns]))
                            underlying_df = pd.DataFrame(underlying_rows, columns=underlying_columns)
                            
                            # Clean Value and Pct columns
                            if 'Value' in underlying_df.columns:
                                underlying_df['Value'] = (underlying_df['Value'].astype(str)
                                                        .str.replace("$", "", regex=False)
                                                        .str.replace(",", "", regex=False))
                                underlying_df['Value'] = pd.to_numeric(underlying_df['Value'], errors='coerce')
                            
                            if 'Pct' in underlying_df.columns:
                                underlying_df['Pct'] = pd.to_numeric(underlying_df['Pct'], errors='coerce')
                            
                            # Save underlying fund data
                            underlying_csv = f"{underlying_ticker}.csv"
                            underlying_df.to_csv(underlying_csv, index=False)
                            print(f"DEBUG: Data written to {underlying_csv}")
                            self.logger.info(f"Data written to {underlying_csv}")
                            
                        except Exception as e:
                            print(f"DEBUG ERROR: Error processing underlying fund {underlying_ticker}: {str(e)}")
                            self.logger.error(f"Error processing underlying fund {underlying_ticker}: {str(e)}")
                            import traceback
                            print(f"DEBUG TRACEBACK: {traceback.format_exc()}")
                            continue
                            
            except Exception as e:
                print(f"DEBUG ERROR: Error processing {ticker}: {str(e)}")
                self.logger.error(f"Error processing {ticker}: {str(e)}")
                import traceback
                print(f"DEBUG TRACEBACK: {traceback.format_exc()}")
                continue 