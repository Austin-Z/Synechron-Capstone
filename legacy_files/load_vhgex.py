"""
Script to load VHGEX fund data into the database.
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.scripts.load_initial_funds import DataLoader

async def main():
    """Load VHGEX fund data into the database."""
    print("Starting to load VHGEX fund data...")
    
    # Create data loader
    loader = DataLoader()
    
    # Load VHGEX fund
    results = await loader.load_funds(["VHGEX"])
    
    # Print results
    print("\nLoading Summary:")
    print(f"Successfully loaded: {len(results['success'])} funds")
    if results['success']:
        print("Success:", ", ".join(results['success']))
    
    print(f"Updated: {len(results['updated'])} funds")
    if results['updated']:
        print("Updated:", ", ".join(results['updated']))
    
    print(f"Failed: {len(results['failed'])} funds")
    if results['failed']:
        print("Failed:", ", ".join(results['failed']))

if __name__ == "__main__":
    asyncio.run(main())
