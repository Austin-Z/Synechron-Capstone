#!/usr/bin/env python
"""
Script to check holdings in the database for a specific fund
"""
from src.database.manager import DatabaseManager
from src.models.database import Fund, Filing, Holding

def check_fund_holdings(ticker):
    """Check holdings for a specific fund ticker"""
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # Check if fund exists
        fund = session.query(Fund).filter(Fund.ticker == ticker).first()
        if not fund:
            print(f"ERROR: Fund {ticker} not found in database")
            return
            
        print(f"Fund {ticker} found with ID {fund.id}")
        
        # Check filings
        filings = session.query(Filing).filter(Filing.fund_id == fund.id).all()
        print(f"Found {len(filings)} filings for {ticker}")
        
        if not filings:
            print(f"ERROR: No filings found for {ticker}")
            return
            
        # Get latest filing
        latest_filing = filings[0]
        print(f"Latest filing ID: {latest_filing.id}, Date: {latest_filing.filing_date}")
        
        # Check holdings
        holdings = session.query(Holding).filter(Holding.filing_id == latest_filing.id).all()
        print(f"Found {len(holdings)} holdings for {ticker} in filing {latest_filing.id}")
        
        # Show sample holdings
        if holdings:
            print("Sample holdings:")
            for i, holding in enumerate(holdings[:5]):
                print(f"  {i+1}. {holding.name} - {holding.ticker} - ${holding.value:,.2f} ({holding.percentage}%)")
        else:
            print(f"ERROR: No holdings found for {ticker}")
            
    finally:
        session.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        ticker = sys.argv[1]
    else:
        ticker = "TRZAX"  # Default ticker to check
        
    check_fund_holdings(ticker)
