from src.services.fund_service import FundService
from src.database.manager import DatabaseManager

def verify_holdings():
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # Check MDIZX holdings
        holdings_df = FundService.get_holdings_details(session, 'MDIZX')
        print("\nMDIZX Holdings:")
        if holdings_df.empty:
            print("No holdings found - database may be empty")
            print("Try running reset_database.py followed by load_initial_funds.py")
            return
            
        print(holdings_df)
        
        # Print total value and count
        total_value = holdings_df['Value'].str.replace('$', '').str.replace(',', '').astype(float).sum()
        print(f"\nTotal Value: ${total_value:,.2f}")
        print(f"Number of Holdings: {len(holdings_df)}")
        
    finally:
        session.close()

if __name__ == "__main__":
    verify_holdings() 