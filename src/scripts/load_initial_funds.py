from src.collectors.edgar_collector import EdgarCollector
from src.services.fund_service import FundService
from src.database.manager import DatabaseManager
import asyncio
import pandas as pd
from typing import List, Dict
import os
from src.utils.logger import setup_logger
from datetime import datetime

class DataLoader:
    """Loads fund data from NPORT filings into database."""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.session = self.db.get_session()
        self.collector = EdgarCollector()
        self.logger = setup_logger('data_loader')
        
    async def load_funds(self, tickers: List[str]) -> Dict:
        """Load fund data into database."""
        results = {
            "success": [],
            "updated": [],
            "failed": []
        }
        
        try:
            self.logger.info(f"Starting NPORT filings collection for tickers: {tickers}")
            print(f"DEBUG: Starting NPORT filings collection for tickers: {tickers}")
            
            try:
                self.collector.retrieve_nport_filings(tickers)
                print(f"DEBUG: NPORT filings collection completed")
            except Exception as e:
                self.logger.error(f"Error during NPORT filings collection: {str(e)}")
                print(f"DEBUG ERROR: Error during NPORT filings collection: {str(e)}")
                import traceback
                print(f"DEBUG TRACEBACK: {traceback.format_exc()}")
            
            for ticker in tickers:
                try:
                    csv_path = f"{ticker}.csv"
                    print(f"DEBUG: Looking for CSV file at {os.path.abspath(csv_path)}")
                    
                    if not os.path.exists(csv_path):
                        self.logger.error(f"CSV file not found for {ticker}")
                        print(f"DEBUG ERROR: CSV file not found for {ticker}")
                        results["failed"].append(ticker)
                        continue
                        
                    # Read CSV data
                    df = pd.read_csv(csv_path)
                    self.logger.info(f"Processing {ticker} with {len(df)} holdings")
                    print(f"DEBUG: Processing {ticker} with {len(df)} holdings")
                    
                    # Check if fund exists
                    existing_fund = FundService.get_fund_by_ticker(self.session, ticker)
                    if existing_fund:
                        self.logger.info(f"Updating existing fund {ticker}...")
                        print(f"DEBUG: Updating existing fund {ticker}...")
                        if FundService.update_fund_holdings(self.session, ticker, df):
                            results["updated"].append(ticker)
                            print(f"DEBUG: Successfully updated {ticker}")
                        else:
                            results["failed"].append(ticker)
                            print(f"DEBUG ERROR: Failed to update {ticker}")
                    else:
                        # Create new fund
                        try:
                            # Extract fund name safely
                            fund_name = ticker  # Default to ticker if name can't be extracted
                            if 'Name' in df.columns and len(df) > 0:
                                fund_name = df['Name'].iloc[0] if not pd.isna(df['Name'].iloc[0]) else ticker
                            
                            print(f"DEBUG: Creating fund with ticker={ticker}, name={fund_name}")
                            
                            # Set fund_type to 'fund_of_funds' for all funds loaded through this script
                            # This ensures they appear in the dashboard's fund selection dropdown
                            fund = FundService.create_or_update_fund(
                                session=self.session,
                                ticker=ticker,
                                name=fund_name,
                                fund_type='fund_of_funds'
                            )
                        except IndexError as ie:
                            print(f"DEBUG ERROR: Index error when extracting fund name: {str(ie)}")
                            print(f"DEBUG: DataFrame shape: {df.shape}, columns: {df.columns.tolist()}")
                            # Still create the fund with ticker as name
                            # Use 'fund_of_funds' type to ensure it appears in the dashboard dropdown
                            fund = FundService.create_or_update_fund(
                                session=self.session,
                                ticker=ticker,
                                name=ticker,
                                fund_type='fund_of_funds'
                            )
                        
                        # Convert total assets to float
                        total_assets = 0.0
                        try:
                            if 'Value' in df.columns and not df.empty:
                                # Handle different Value formats
                                if pd.api.types.is_numeric_dtype(df['Value']):
                                    total_assets = float(df['Value'].sum())
                                else:
                                    # Try to convert string values
                                    value_str = str(df['Value'].sum()).replace('$', '').replace(',', '')
                                    total_assets = float(value_str)
                                print(f"DEBUG: Calculated total assets: {total_assets}")
                            else:
                                print(f"DEBUG: No Value column found or empty dataframe, using default total_assets=0")
                        except Exception as e:
                            print(f"DEBUG ERROR: Error calculating total assets: {str(e)}")
                            # Continue with default total_assets=0
                        
                        # Create filing with proper datetime objects
                        filing = FundService.create_filing(
                            session=self.session,
                            fund=fund,
                            filing_date=datetime.now(),
                            period_end_date=datetime.now(),
                            total_assets=total_assets
                        )
                        
                        try:
                            print(f"DEBUG: Creating holdings for {ticker} with {len(df)} rows")
                            holdings = FundService.create_holdings(
                                session=self.session,
                                filing=filing,
                                holdings_df=df
                            )
                            print(f"DEBUG: Successfully created {len(holdings) if holdings else 0} holdings")
                        except Exception as e:
                            print(f"DEBUG ERROR: Error creating holdings: {str(e)}")
                            import traceback
                            print(f"DEBUG TRACEBACK: {traceback.format_exc()}")
                            # Continue with the process even if holdings creation fails
                            # The fund and filing will still be in the database
                        
                        results["success"].append(ticker)
                    
                    self.logger.info(f"Successfully processed {ticker}")
                    print(f"DEBUG: Successfully processed {ticker}")
                    
                except Exception as e:
                    self.logger.error(f"Error processing {ticker}: {str(e)}")
                    print(f"DEBUG ERROR: Error processing {ticker}: {str(e)}")
                    results["failed"].append(ticker)
                    self.session.rollback()
                    print(f"DEBUG: Rolling back session due to error")
                    continue
                    
            return results
            
        finally:
            self.session.close()
            print(f"DEBUG: Closing database session")
            # Clean up any remaining CSV files
            for f in os.listdir():
                if f.endswith('.csv'):
                    try:
                        os.remove(f)
                    except Exception as e:
                        self.logger.error(f"Error removing file {f}: {str(e)}")
                        print(f"DEBUG ERROR: Error removing file {f}: {str(e)}")

async def main():
    """Main function to load initial fund data."""
    tickers = ["MDIZX", "TSVPX", "PFDOX", 'UPAAX', 'GLEAX', 'LIONX', 'MHESX', 
    'RHSAX', 'APITX', 'SMIFX']
    
    loader = DataLoader()
    results = await loader.load_funds(tickers)
    
    # Print results
    print("\nLoading Summary:")
    print(f"Successfully loaded: {len(results['success'])} funds")
    if results['success']:
        print("Success:", ", ".join(results['success']))
    
    print(f"\nUpdated: {len(results['updated'])} funds")
    if results['updated']:
        print("Updated:", ", ".join(results['updated']))
    
    print(f"\nFailed to load: {len(results['failed'])} funds")
    if results['failed']:
        print("Failed:", ", ".join(results['failed']))

if __name__ == "__main__":
    asyncio.run(main()) 