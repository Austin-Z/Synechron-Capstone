import pytest
from datetime import datetime
from src.database.manager import DatabaseManager
from src.services.fund_service import FundService
from src.models.database import Fund, Filing, Holding
import pandas as pd

@pytest.fixture
def db_manager():
    return DatabaseManager()

@pytest.fixture
def session(db_manager):
    session = db_manager.get_session()
    yield session
    session.close()

def test_create_fund(session):
    # Test fund creation
    fund = FundService.create_or_update_fund(
        session=session,
        ticker="TEST",
        name="Test Fund",
        fund_type="FOF"
    )
    
    assert fund.ticker == "TEST"
    assert fund.name == "Test Fund"
    assert fund.fund_type == "FOF"

def test_create_filing(session):
    # Create a fund first
    fund = FundService.create_or_update_fund(
        session=session,
        ticker="TEST",
        name="Test Fund",
        fund_type="FOF"
    )
    
    # Test filing creation
    filing = FundService.create_filing(
        session=session,
        fund=fund,
        filing_date=datetime.utcnow(),
        period_end_date=datetime.utcnow(),
        total_assets=1000000.0
    )
    
    assert filing.fund_id == fund.id
    assert filing.total_assets == 1000000.0

def test_create_holdings(session):
    # Create test data
    fund = FundService.create_or_update_fund(
        session=session,
        ticker="TEST",
        name="Test Fund",
        fund_type="FOF"
    )
    
    filing = FundService.create_filing(
        session=session,
        fund=fund,
        filing_date=datetime.utcnow(),
        period_end_date=datetime.utcnow(),
        total_assets=1000000.0
    )
    
    # Create test DataFrame
    df = pd.DataFrame({
        'Name': ['Test Holding'],
        'Value': [100000.0],
        'Pct': [10.0],
        'Category': ['EQUITY']
    })
    
    # Test holdings creation
    holdings = FundService.create_holdings(
        session=session,
        filing=filing,
        holdings_df=df
    )
    
    assert len(holdings) == 1
    assert holdings[0].name == 'Test Holding'
    assert holdings[0].value == 100000.0 