import os
import sys
import pandas as pd
from datetime import datetime, timedelta, date
import random

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.manager import DatabaseManager
from src.models.institutional_holdings import Institute13F, InstitutionalHolding
from src.services.fund_service import FundService

# Sample institutional investors
SAMPLE_INSTITUTIONS = [
    {"name": "BlackRock Inc."},
    {"name": "Vanguard Group Inc."},
    {"name": "State Street Corporation"}
]

def create_institution(session, name, report_date):
    """Create an institution record."""
    institution = Institute13F(
        institution_name=name,
        report_date=report_date,
        created_at=datetime.utcnow()
    )
    session.add(institution)
    session.commit()
    return institution

def create_holdings(session, institution_id, holdings_data):
    """Create holdings records for an institution."""
    created_count = 0
    batch_size = 20  # Process in smaller batches
    
    for i in range(0, len(holdings_data), batch_size):
        batch = holdings_data.iloc[i:i+batch_size]
        
        for _, row in batch.iterrows():
            try:
                # Handle nan values by converting them to None
                ticker = row.get('Ticker')
                cusip = row.get('Cusip')
                name = row.get('Name')
                value = row.get('Value_Numeric')
                shares = row.get('Shares', 0)
                pct = row.get('Pct', 0)
                
                # Convert nan to None
                if pd.isna(ticker):
                    ticker = None
                if pd.isna(cusip):
                    cusip = None
                if pd.isna(name):
                    name = None
                if pd.isna(value):
                    value = 0.0
                if pd.isna(shares):
                    shares = 0
                if pd.isna(pct):
                    pct = 0.0
                
                holding = InstitutionalHolding(
                    report_id=institution_id,
                    ticker=ticker,
                    cusip=cusip,
                    issuer_name=name,
                    security_class='Equity',  # Default to Equity
                    value=value,
                    shares=int(shares) if shares else 0,
                    percentage=pct,
                    created_at=datetime.utcnow()
                )
                session.add(holding)
                created_count += 1
            except Exception as e:
                print(f"Error creating holding for {row.get('Name')}: {str(e)}")
        
        # Commit after each batch
        try:
            session.commit()
            print(f"Committed batch of {len(batch)} holdings")
        except Exception as e:
            print(f"Error committing batch: {str(e)}")
            session.rollback()
    
    return created_count

def get_fund_holdings(session, ticker):
    """Get holdings for a fund and prepare them for institutional holdings."""
    holdings = FundService.get_holdings_details(session, ticker)
    if holdings.empty:
        return pd.DataFrame()
    
    # Add Value_Numeric column if it doesn't exist
    if 'Value_Numeric' not in holdings.columns:
        holdings['Value_Numeric'] = holdings['Value'].str.replace('$', '').str.replace(',', '').astype(float)
    
    # Add Shares column (simulated)
    holdings['Shares'] = holdings['Value_Numeric'].apply(lambda x: int(x * random.uniform(10, 100)))
    
    return holdings

def create_sample_institutional_data(session):
    """Create sample institutional data based on existing fund holdings."""
    # Get reference fund holdings (MDIZX)
    mdizx_holdings = get_fund_holdings(session, "MDIZX")
    if mdizx_holdings.empty:
        print("No holdings found for MDIZX. Cannot create sample institutional data.")
        return
    
    # Current date for reports
    current_date = date.today()
    
    # Create institutions and holdings for each
    for inst_data in SAMPLE_INSTITUTIONS:
        # Create institution with a recent report date
        report_date = current_date - timedelta(days=random.randint(30, 90))
        institution = create_institution(session, inst_data["name"], report_date)
        
        # Create holdings based on MDIZX holdings with some variations
        inst_holdings = mdizx_holdings.copy()
        
        # Randomly select 70-90% of the holdings
        sample_size = int(len(inst_holdings) * random.uniform(0.7, 0.9))
        inst_holdings = inst_holdings.sample(sample_size)
        
        # Adjust values to simulate different institutional positions
        scale_factor = random.uniform(50, 200)
        inst_holdings['Value_Numeric'] = inst_holdings['Value_Numeric'] * scale_factor
        inst_holdings['Pct'] = inst_holdings['Pct'] * random.uniform(0.8, 1.2)
        
        # Add some random holdings not in MDIZX
        additional_holdings = []
        for i in range(random.randint(5, 15)):
            ticker = f"TICKER{i}"
            name = f"Random Stock {i}"
            value = random.uniform(1000000, 10000000)
            shares = int(value * random.uniform(10, 100))
            pct = random.uniform(0.1, 2.0)
            
            additional_holdings.append({
                'Ticker': ticker,
                'Name': name,
                'Cusip': None,  # Explicitly set Cusip to None for random stocks
                'Value_Numeric': value,
                'Shares': shares,
                'Pct': pct
            })
        
        additional_df = pd.DataFrame(additional_holdings)
        inst_holdings = pd.concat([inst_holdings, additional_df], ignore_index=True)
        
        # Create holdings records
        created_count = create_holdings(session, institution.id, inst_holdings)
        
        print(f"Created {created_count} holdings for {institution.institution_name}")

if __name__ == "__main__":
    # Initialize database connection
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # Create sample institutional data
        create_sample_institutional_data(session)
        print("Sample institutional data created successfully.")
    except Exception as e:
        import traceback
        print(f"Error creating sample institutional data: {str(e)}")
        print("Full error:")
        traceback.print_exc()
    finally:
        session.close()
