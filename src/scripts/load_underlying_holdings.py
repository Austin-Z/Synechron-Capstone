from src.services.fund_service import FundService
from src.database.manager import DatabaseManager
from src.collectors.edgar_collector import EdgarCollector
import pandas as pd
from src.utils.logger import setup_logger
from datetime import datetime

logger = setup_logger('underlying_holdings')

def load_underlying_holdings():
    """Load holdings for underlying funds and their relationships."""
    db = DatabaseManager()
    session = db.get_session()
    collector = EdgarCollector()
    
    try:
        # Get all fund tickers from the database
        all_tickers = FundService.get_all_fund_tickers(session)
        logger.info(f"Processing {len(all_tickers)} funds: {all_tickers}")
        
        # Create CUSIP to ticker mapping for all funds
        cusip_ticker_map = {}
        all_cusips = []
        
        # Process each fund to collect all CUSIPs
        for ticker in all_tickers:
            try:
                fund_holdings = FundService.get_holdings_details(session, ticker)
                if fund_holdings.empty:
                    logger.warning(f"No holdings found for {ticker}")
                    continue
                    
                logger.info(f"\n{ticker} Fund Structure:")
                logger.info(f"Total Holdings: {len(fund_holdings)}")
                
                if 'Cusip' in fund_holdings.columns:
                    fund_cusips = fund_holdings['Cusip'].tolist()
                    fund_cusips = [c for c in fund_cusips if c and str(c).upper() != 'NONE']
                    all_cusips.extend(fund_cusips)
                else:
                    logger.warning(f"No Cusip column found in {ticker} holdings")
            except Exception as e:
                logger.error(f"Error processing {ticker} holdings: {str(e)}")
        
        # Remove duplicates
        all_cusips = list(set(all_cusips))
        logger.info(f"Found {len(all_cusips)} unique CUSIPs across all funds")
        
        # Get tickers for all CUSIPs
        cusip_map = collector.cusip_to_ticker(all_cusips)
        for cusip, ticker in cusip_map.items():
            if ticker != 'Not Found':
                cusip_ticker_map[cusip] = ticker
        
        # Update parent fund holdings with correct tickers
        for cusip, ticker in cusip_ticker_map.items():
            FundService.update_holding_ticker(
                session=session,
                cusip=cusip,
                ticker=ticker
            )
        
        # Get unique tickers for underlying funds
        underlying_tickers = list(cusip_ticker_map.values())
        logger.info(f"Found {len(underlying_tickers)} underlying funds")
        
        # Collect NPORT filings for underlying funds
        collector.retrieve_nport_filings(underlying_tickers)
        
        # Process each underlying fund
        for ticker in underlying_tickers:
            try:
                csv_path = f"{ticker}.csv"
                if not pd.io.common.file_exists(csv_path):
                    logger.error(f"CSV file not found for {ticker}")
                    continue
                
                # Read underlying fund data
                df = pd.read_csv(csv_path)
                logger.info(f"\nProcessing {ticker} with {len(df)} holdings")
                
                # Create or update fund record
                fund = FundService.create_or_update_fund(
                    session=session,
                    ticker=ticker,
                    name=df['Name'].iloc[0] if 'Name' in df.columns else ticker,
                    fund_type='Mutual Fund'
                )
                
                # Create filing
                total_assets = 0.0
                if 'Value' in df.columns:
                    value_str = str(df['Value'].sum()).replace('$', '').replace(',', '')
                    total_assets = float(value_str)
                
                filing = FundService.create_filing(
                    session=session,
                    fund=fund,
                    filing_date=datetime.now(),
                    period_end_date=datetime.now(),
                    total_assets=total_assets
                )
                
                # Create holdings
                holdings = FundService.create_holdings(
                    session=session,
                    filing=filing,
                    holdings_df=df
                )
                
                logger.info(f"Successfully loaded {ticker} with {len(holdings)} holdings")
                
            except Exception as e:
                logger.error(f"Error processing {ticker}: {str(e)}")
                session.rollback()
                continue
                
    finally:
        session.close()

if __name__ == "__main__":
    load_underlying_holdings() 