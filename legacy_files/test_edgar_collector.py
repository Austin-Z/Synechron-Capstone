import asyncio
import pytest
from src.collectors.edgar_collector import EdgarCollector

async def test_collector():
    """Test the EdgarCollector with sample tickers."""
    collector = EdgarCollector()
    
    # Test tickers
    tickers = ["MDIZX", "TSVPX", "PFDOX"]
    
    try:
        result = await collector.collect_fof_holdings(tickers)
        
        # Print summary
        print("\nProcessing Summary:")
        print(f"Successfully processed: {len(result['summary']['success'])} funds")
        print(f"No filings found: {len(result['summary']['no_filings'])} funds")
        print(f"Errors encountered: {len(result['summary']['errors'])} funds")
        
        # Print results
        for ticker, df in result['data'].items():
            print(f"\nHoldings for {ticker}:")
            print(f"Number of holdings: {len(df)}")
            print("Sample data:")
            print(df.head())
            
    except Exception as e:
        print(f"Error during testing: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_collector()) 