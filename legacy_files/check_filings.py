#!/usr/bin/env python
"""
Script to check filings in the database for a specific fund
"""
from src.database.manager import DatabaseManager
from src.models.database import Fund, Filing
import sys

def check_fund_filings(ticker):
    """Check filings for a specific fund ticker"""
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # Check if fund exists
        fund = session.query(Fund).filter(Fund.ticker == ticker).first()
        if not fund:
            print(f"ERROR: Fund {ticker} not found in database")
            return
            
        print(f"Fund {ticker} found with ID {fund.id}")
        
        # Get all filings sorted by date
        filings = sorted(fund.filings, key=lambda x: x.filing_date, reverse=True)
        print(f"Found {len(filings)} filings for {ticker}")
        
        # Show filings
        for i, filing in enumerate(filings[:10]):  # Show up to 10 filings
            print(f"Filing {i+1}: ID={filing.id}, Date={filing.filing_date}, Holdings={len(filing.holdings)}")
            
    finally:
        session.close()

if __name__ == "__main__":
    ticker = "MDIZX"  # Default ticker to check
    
    if len(sys.argv) > 1:
        ticker = sys.argv[1]
        
    check_fund_filings(ticker)
