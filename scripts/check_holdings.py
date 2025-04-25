import os
import sys
import pandas as pd

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.manager import DatabaseManager
from src.services.fund_service import FundService
from src.services.institutional_service import InstitutionalService

def check_holdings():
    """Check the holdings data for MDIZX and institutions."""
    # Initialize database connection
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # Get MDIZX holdings
        mdizx_holdings = FundService.get_holdings_details(session, "MDIZX")
        print(f"MDIZX holdings count: {len(mdizx_holdings)}")
        print("\nSample MDIZX holdings:")
        if not mdizx_holdings.empty:
            print(mdizx_holdings[['Name', 'Ticker', 'Cusip', 'Value']].head(10))
        else:
            print("No holdings found for MDIZX")
        
        # Get underlying securities of MDIZX
        print("\n\nGetting underlying securities for MDIZX's direct holdings...")
        all_underlying = pd.DataFrame()
        
        for _, holding in mdizx_holdings.iterrows():
            if holding['Ticker'] and str(holding['Ticker']).upper() != 'NONE':
                print(f"\nChecking underlying holdings for {holding['Name']} ({holding['Ticker']})")
                # Get holdings of this underlying fund
                underlying = FundService.get_holdings_details(session, holding['Ticker'])
                if not underlying.empty:
                    print(f"Found {len(underlying)} underlying securities")
                    # Add parent fund info
                    underlying['Parent_Fund'] = holding['Name']
                    underlying['Parent_Ticker'] = holding['Ticker']
                    
                    # Append to all underlying securities
                    all_underlying = pd.concat([all_underlying, underlying])
                else:
                    print(f"No holdings found for {holding['Ticker']}")
        
        print(f"\nTotal underlying securities: {len(all_underlying)}")
        if not all_underlying.empty:
            print("\nSample underlying securities:")
            display_cols = ['Name', 'Ticker', 'Cusip', 'Value', 'Parent_Fund']
            available_cols = [col for col in display_cols if col in all_underlying.columns]
            print(all_underlying[available_cols].head(10))
        
        # Get all institutions
        institutions = InstitutionalService.get_all_institutions(session)
        
        for inst in institutions:
            print(f"\n\nInstitution: {inst['name']} (ID: {inst['id']})")
            
            # Get institution holdings
            inst_holdings = InstitutionalService.get_institution_holdings(session, inst['id'])
            print(f"Holdings count: {len(inst_holdings)}")
            
            print("\nSample institution holdings:")
            if not inst_holdings.empty:
                print(inst_holdings[['Name', 'Ticker', 'Cusip', 'Value']].head(10))
            else:
                print("No holdings found for this institution")
            
            # Check for matching tickers between underlying securities and institution holdings
            if not all_underlying.empty and not inst_holdings.empty:
                # Check for ticker matches
                underlying_tickers = set(all_underlying['Ticker'].dropna())
                inst_tickers = set(inst_holdings['Ticker'].dropna())
                common_tickers = underlying_tickers.intersection(inst_tickers)
                
                print(f"\nCommon tickers between underlying securities and institution: {len(common_tickers)}")
                if common_tickers:
                    print("Sample common tickers:", list(common_tickers)[:10])
                    
                    # Show some examples of matching securities
                    print("\nSample matching securities:")
                    for ticker in list(common_tickers)[:5]:
                        underlying_match = all_underlying[all_underlying['Ticker'] == ticker].iloc[0]
                        inst_match = inst_holdings[inst_holdings['Ticker'] == ticker].iloc[0]
                        
                        print(f"\nTicker: {ticker}")
                        print(f"Underlying security: {underlying_match['Name']} (from {underlying_match['Parent_Fund']})")
                        print(f"Institution holding: {inst_match['Name']}")
                
                # Check for potential name matches
                print("\nSample name comparisons:")
                for i, fund_row in mdizx_holdings.head(5).iterrows():
                    fund_name = fund_row['Name']
                    print(f"\nFund holding: {fund_name}")
                    
                    # Find similar names in institution holdings
                    for j, inst_row in inst_holdings.head(20).iterrows():
                        inst_name = inst_row['Name']
                        if fund_name and inst_name and fund_name.lower() in inst_name.lower() or inst_name.lower() in fund_name.lower():
                            print(f"  Potential match: {inst_name}")
    
    except Exception as e:
        import traceback
        print(f"Error checking holdings: {str(e)}")
        print("Full error:")
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    check_holdings()
