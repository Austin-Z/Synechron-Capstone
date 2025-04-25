import pytest
import asyncio
from datetime import datetime
from src.collectors.edgar_collector import EdgarCollector
from src.database.manager import DatabaseManager
from src.services.fund_service import FundService
from sqlalchemy.orm import Session

@pytest.fixture
def db_manager():
    manager = DatabaseManager()
    # Create tables if they don't exist
    manager.create_tables()
    return manager

@pytest.fixture
def session(db_manager):
    session = db_manager.get_session()
    yield session
    session.close()

@pytest.fixture
def collector():
    return EdgarCollector()

async def test_full_collection_flow(collector: EdgarCollector, session: Session):
    """Test the full flow from NPORT collection to database storage."""
    # Test tickers (one FOF and one regular fund)
    test_tickers = ["MDIZX", "MRSKX"]
    
    try:
        # Collect holdings data
        result = await collector.collect_fof_holdings(test_tickers)
        assert result is not None
        assert len(result['data']) > 0
        
        # Store in database
        await collector.store_holdings_data(result)
        
        # Verify data in database
        for ticker in test_tickers:
            fund = session.query(Fund).filter_by(ticker=ticker).first()
            assert fund is not None
            assert fund.filings is not None
            assert len(fund.filings) > 0
            
            # Check holdings
            latest_filing = fund.filings[0]
            assert len(latest_filing.holdings) > 0
            
            # Check relationships if it's a FOF
            if fund.fund_type == 'FOF':
                assert len(fund.holdings_as_parent) > 0

    except Exception as e:
        pytest.fail(f"Test failed: {str(e)}")

async def test_bulk_data_loading(collector: EdgarCollector, session: Session):
    """Test performance of bulk data loading."""
    # Test with a larger set of tickers
    test_tickers = ["MDIZX", "TSVPX", "PFDOX", "MRSKX", "MEMJX", "MKVHX", "MINJX", "MGRDX", "MIDLX"]
    
    try:
        start_time = datetime.now()
        
        # Collect holdings data
        result = await collector.collect_fof_holdings(test_tickers)
        collection_time = datetime.now() - start_time
        
        # Store in database
        db_start_time = datetime.now()
        await collector.store_holdings_data(result)
        db_time = datetime.now() - db_start_time
        
        total_time = datetime.now() - start_time
        
        # Log performance metrics
        print(f"\nPerformance Metrics:")
        print(f"Data Collection Time: {collection_time.total_seconds():.2f}s")
        print(f"Database Storage Time: {db_time.total_seconds():.2f}s")
        print(f"Total Processing Time: {total_time.total_seconds():.2f}s")
        print(f"Total Funds Processed: {len(result['data'])}")
        
        # Verify all data was stored
        for ticker in test_tickers:
            fund = session.query(Fund).filter_by(ticker=ticker).first()
            assert fund is not None
            
    except Exception as e:
        pytest.fail(f"Performance test failed: {str(e)}")

async def test_error_handling(collector: EdgarCollector, session: Session):
    """Test error handling in various scenarios."""
    
    # Test invalid ticker
    result = await collector.collect_fof_holdings(["INVALID"])
    assert "INVALID" in result['summary']['no_filings']
    
    # Test network error (modify API key temporarily)
    original_key = collector.openfigi_api_key
    collector.openfigi_api_key = "invalid_key"
    result = await collector.collect_fof_holdings(["MDIZX"])
    assert len(result['summary']['errors']) > 0
    collector.openfigi_api_key = original_key
    
    # Test database connection error
    with pytest.raises(Exception):
        # Force a database error by closing the session
        session.close()
        await collector.store_holdings_data({"data": {"TEST": None}})

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 