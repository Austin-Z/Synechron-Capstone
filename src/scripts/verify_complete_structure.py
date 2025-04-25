from src.services.fund_service import FundService
from src.database.manager import DatabaseManager
from src.utils.logger import setup_logger

logger = setup_logger('complete_structure')

def verify_complete_structure():
    """Verify all levels of fund holdings are in database."""
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # Level 1: Parent Fund
        mdizx = FundService.get_holdings_details(session, 'MDIZX')
        total_parent_value = mdizx['Value'].str.replace('$', '').str.replace(',', '').astype(float).sum()
        logger.info(f"\nLevel 1: MDIZX")
        logger.info(f"Total Value: ${total_parent_value:,.2f}")
        logger.info(f"Direct Holdings: {len(mdizx)}")
        
        # Level 2: Underlying Funds
        total_underlying_holdings = 0
        underlying_value = 0
        
        for _, holding in mdizx.iterrows():
            ticker = holding['Ticker']
            if ticker and ticker != 'None':
                underlying = FundService.get_holdings_details(session, ticker)
                holdings_count = len(underlying)
                total_underlying_holdings += holdings_count
                
                value = float(str(holding['Value']).replace('$', '').replace(',', ''))
                underlying_value += value
                
                logger.info(f"\n{ticker}:")
                logger.info(f"Holdings: {holdings_count}")
                logger.info(f"Value: ${value:,.2f}")
                logger.info(f"Percentage: {holding['Pct']}%")
                
                # Show first 3 holdings as sample
                if not underlying.empty:
                    logger.info("Sample Holdings:")
                    for _, stock in underlying.head(3).iterrows():
                        logger.info(f"  {stock['Name']}: {stock['Value']} ({stock['Pct']}%)")
        
        logger.info(f"\nSummary:")
        logger.info(f"Total Underlying Funds: {len(mdizx)}")
        logger.info(f"Total Underlying Holdings: {total_underlying_holdings}")
        logger.info(f"Total Value Verified: ${underlying_value:,.2f}")
        
    finally:
        session.close()

if __name__ == "__main__":
    verify_complete_structure() 