from src.services.fund_service import FundService
from src.database.manager import DatabaseManager
from src.collectors.edgar_collector import EdgarCollector
import pandas as pd
from src.utils.logger import setup_logger
from datetime import datetime
import argparse
import sys
from src.models.database import Filing, FundRelationship

logger = setup_logger('underlying_holdings')

def load_underlying_holdings(specific_ticker=None):
    """Load holdings for underlying funds and their relationships.
    
    Args:
        specific_ticker: Optional ticker symbol to process only a specific fund
    """
    db = DatabaseManager()
    session = db.get_session()
    collector = EdgarCollector()
    
    try:
        # Get fund tickers to process
        if specific_ticker:
            all_tickers = [specific_ticker]
            logger.info(f"Processing specific fund: {specific_ticker}")
        else:
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
        
        # Map CUSIPs to tickers and update the database
        logger.info(f"Found {len(cusip_ticker_map)} mapped CUSIPs to tickers")
        
        # Get direct holdings that have tickers
        direct_holding_tickers = []
        
        # Process each parent fund
        for parent_ticker in all_tickers:
            try:
                # Get the parent fund
                parent_fund = FundService.get_fund_by_ticker(session, parent_ticker)
                if not parent_fund:
                    logger.warning(f"Parent fund {parent_ticker} not found in database")
                    continue
                
                # Get the latest filing for this fund
                parent_filing = session.query(Filing).filter(Filing.fund_id == parent_fund.id).order_by(Filing.filing_date.desc()).first()
                if not parent_filing:
                    logger.warning(f"No filing found for {parent_ticker}")
                    continue
                
                # Get holdings for this fund
                parent_holdings = FundService.get_holdings_details(session, parent_ticker)
                if parent_holdings.empty:
                    logger.warning(f"No holdings found for {parent_ticker}")
                    continue
                
                # Create fund relationships for each holding that has a ticker
                relationships_created = 0
                for _, row in parent_holdings.iterrows():
                    cusip = row.get('Cusip')
                    ticker = row.get('Ticker')
                    
                    # Skip if we don't have a ticker
                    if pd.isna(ticker) or ticker == '':
                        continue
                    
                    # Add to the list of direct holding tickers
                    direct_holding_tickers.append(ticker)
                    
                    # Get or create the child fund
                    child_fund = FundService.get_fund_by_ticker(session, ticker)
                    if not child_fund:
                        # Create a new fund record for this ticker
                        child_fund = FundService.create_or_update_fund(
                            session=session,
                            ticker=ticker,
                            name=row.get('Name', ticker),
                            fund_type='underlying_fund'  # Mark as underlying fund
                        )
                    
                    # Check if relationship already exists
                    existing_relationship = session.query(FundRelationship).filter(
                        FundRelationship.parent_fund_id == parent_fund.id,
                        FundRelationship.child_fund_id == child_fund.id,
                        FundRelationship.filing_id == parent_filing.id
                    ).first()
                    
                    if not existing_relationship:
                        # Create a new relationship
                        relationship = FundRelationship(
                            parent_fund_id=parent_fund.id,
                            child_fund_id=child_fund.id,
                            filing_id=parent_filing.id,
                            percentage=float(row.get('Percentage', 0)) if not pd.isna(row.get('Percentage', 0)) else 0,
                            value=float(str(row.get('Value', '0')).replace('$', '').replace(',', '')) if not pd.isna(row.get('Value', 0)) else 0
                        )
                        session.add(relationship)
                        relationships_created += 1
                
                logger.info(f"Created {relationships_created} fund relationships for {parent_ticker}")
                session.commit()
                
            except Exception as e:
                logger.error(f"Error processing relationships for {parent_ticker}: {str(e)}")
                session.rollback()
                continue
        
        # Now retrieve NPORT filings for direct holdings (but not for their underlying securities)
        if direct_holding_tickers:
            logger.info(f"Retrieving NPORT filings for {len(direct_holding_tickers)} direct holdings")
            unique_direct_holdings = list(set(direct_holding_tickers))  # Remove duplicates
            
            # Retrieve NPORT filings for direct holdings
            collector.retrieve_nport_filings(unique_direct_holdings)
            
            # Process each direct holding's NPORT filing
            direct_holdings_processed = 0
            for ticker in unique_direct_holdings:
                try:
                    csv_path = f"{ticker}.csv"
                    if not pd.io.common.file_exists(csv_path):
                        logger.warning(f"CSV file not found for direct holding {ticker}")
                        continue
                    
                    # Read direct holding data
                    df = pd.read_csv(csv_path)
                    logger.info(f"Processing direct holding {ticker} with {len(df)} securities")
                    
                    # Get the fund record
                    fund = FundService.get_fund_by_ticker(session, ticker)
                    if not fund:
                        logger.warning(f"Fund record not found for {ticker}")
                        continue
                    
                    # Create filing
                    total_assets = 0.0
                    if 'Value' in df.columns:
                        try:
                            value_str = str(df['Value'].sum()).replace('$', '').replace(',', '')
                            total_assets = float(value_str)
                        except Exception as e:
                            logger.warning(f"Error calculating total assets for {ticker}: {str(e)}")
                    
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
                    
                    direct_holdings_processed += 1
                    logger.info(f"Successfully loaded direct holding {ticker} with {len(holdings)} securities")
                    
                except Exception as e:
                    logger.error(f"Error processing direct holding {ticker}: {str(e)}")
                    session.rollback()
                    continue
            
            logger.info(f"Successfully processed {direct_holdings_processed} direct holdings")
                
    finally:
        session.close()

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Load underlying holdings for funds')
    parser.add_argument('--ticker', '-t', type=str, help='Specific fund ticker to process')
    args = parser.parse_args()
    
    # Run with specific ticker if provided
    if args.ticker:
        logger.info(f"Starting processing for specific fund: {args.ticker}")
        load_underlying_holdings(args.ticker)
    else:
        logger.info("Starting processing for all funds")
        load_underlying_holdings()