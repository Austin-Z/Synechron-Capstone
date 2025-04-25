#!/usr/bin/env python
"""
Update fund types in the database.
This script updates the fund_type field for funds in the database.
"""

from src.database.manager import DatabaseManager
from src.models.database import Fund

def update_fund_types():
    """Update fund types in the database."""
    # Define which funds are fund-of-funds
    fund_of_funds = ["MDIZX", "TSVPX", "PFDOX", "UPAAX", "GLEAX", "LIONX", "MHESX", 
                     "RHSAX", "APITX", "SMIFX"]
    
    # Connect to the database
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # Get all funds
        all_funds = session.query(Fund).all()
        
        # Update fund types
        for fund in all_funds:
            if fund.ticker in fund_of_funds:
                if fund.fund_type != 'fund_of_funds':
                    fund.fund_type = 'fund_of_funds'
                    print(f"Updated {fund.ticker} to fund_of_funds")
            else:
                if fund.fund_type != 'underlying_fund':
                    fund.fund_type = 'underlying_fund'
                    print(f"Updated {fund.ticker} to underlying_fund")
        
        # Commit changes
        session.commit()
        print(f"\nSuccessfully updated fund types for {len(all_funds)} funds")
        
    except Exception as e:
        print(f"Error updating fund types: {str(e)}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    update_fund_types()
