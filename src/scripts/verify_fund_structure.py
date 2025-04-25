from src.services.fund_service import FundService
from src.database.manager import DatabaseManager
from src.utils.logger import setup_logger

logger = setup_logger('verify_structure')

def verify_fund_structure():
    """Verify the complete fund structure is loaded correctly."""
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # Check parent fund
        mdizx = FundService.get_holdings_details(session, 'MDIZX')
        logger.info(f"\nMDIZX Holdings: {len(mdizx)}")
        
        # Check each underlying fund
        for _, holding in mdizx.iterrows():
            cusip = holding['Cusip']
            ticker = holding['Ticker']
            name = holding['Name']
            logger.info(f"\nFund: {name}")
            logger.info(f"CUSIP: {cusip}")
            logger.info(f"Ticker: {ticker}")
            logger.info(f"Total Value: {holding['Value']}")
            logger.info(f"Percentage: {holding['Pct']}%")
            
            if ticker and ticker != 'None':
                underlying = FundService.get_holdings_details(session, ticker)
                logger.info(f"Underlying Holdings: {len(underlying)}")
                if len(underlying) > 0:
                    logger.info("Top 5 holdings:")
                    for _, stock in underlying.head().iterrows():
                        logger.info(f"  {stock['Name']}: {stock['Value']} ({stock['Pct']}%)")
    
    finally:
        session.close()

if __name__ == "__main__":
    verify_fund_structure() 