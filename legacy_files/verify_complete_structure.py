from src.services.fund_service import FundService
from src.database.manager import DatabaseManager
from src.utils.logger import setup_logger
import pandas as pd

logger = setup_logger('complete_structure')

def verify_complete_structure(ticker='MDIZX'):
    """Verify all levels of fund holdings are in database.
    
    Args:
        ticker: The ticker symbol of the parent fund to verify (default: MDIZX)
    """
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # Level 1: Parent Fund
        parent_fund = FundService.get_holdings_details(session, ticker)
        if parent_fund.empty:
            logger.error(f"No holdings found for {ticker}")
            return
            
        try:
            total_parent_value = parent_fund['Value'].str.replace('$', '').str.replace(',', '').astype(float).sum()
        except Exception as e:
            logger.warning(f"Error calculating total value: {str(e)}")
            total_parent_value = 0
            
        logger.info(f"\nLevel 1: {ticker}")
        logger.info(f"Total Value: ${total_parent_value:,.2f}")
        logger.info(f"Direct Holdings: {len(parent_fund)}")
        
        # Level 2: Underlying Funds
        total_underlying_holdings = 0
        underlying_value = 0
        
        for _, holding in parent_fund.iterrows():
            child_ticker = holding.get('Ticker')
            if child_ticker and child_ticker != 'None' and not pd.isna(child_ticker):
                underlying = FundService.get_holdings_details(session, child_ticker)
                holdings_count = len(underlying)
                total_underlying_holdings += holdings_count
                
                try:
                    value_str = str(holding.get('Value', '0')).replace('$', '').replace(',', '')
                    value = float(value_str) if value_str else 0.0
                except Exception as e:
                    logger.warning(f"Error parsing value for {child_ticker}: {str(e)}")
                    value = 0.0
                    
                underlying_value += value
                
                logger.info(f"\n{child_ticker}:")
                logger.info(f"Holdings: {holdings_count}")
                logger.info(f"Value: ${value:,.2f}")
                logger.info(f"Percentage: {holding.get('Pct', 0)}%")
                
                # Show first 3 holdings as sample
                if not underlying.empty:
                    logger.info("Sample Holdings:")
                    for _, stock in underlying.head(3).iterrows():
                        name = stock.get('Name', 'Unknown')
                        stock_value = stock.get('Value', '$0')
                        pct = stock.get('Pct', 0)
                        logger.info(f"  {name}: {stock_value} ({pct}%)")
        
        logger.info(f"\nSummary:")
        logger.info(f"Total Underlying Funds: {len(parent_fund)}")
        logger.info(f"Total Underlying Holdings: {total_underlying_holdings}")
        logger.info(f"Total Value Verified: ${underlying_value:,.2f}")
        
    finally:
        session.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Verify complete fund structure')
    parser.add_argument('--ticker', type=str, default='MDIZX', help='Ticker symbol of the parent fund to verify')
    args = parser.parse_args()
    
    verify_complete_structure(args.ticker)