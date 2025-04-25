#!/usr/bin/env python
"""
FOFs-Capstone Complete Workflow Runner

This script provides a single entry point to run the complete workflow:
1. Reset the database (optional)
2. Load initial fund data
3. Load underlying holdings
4. Run the dashboard

Usage:
    python run_all.py [--reset-db] [--skip-data-load] [--verify]

Options:
    --reset-db: Reset the database before loading data
    --skip-data-load: Skip data loading and just run the dashboard
    --verify: Run verification scripts after data loading
"""

import os
import sys
import asyncio
import argparse
import subprocess
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Load environment variables
load_dotenv()

# Import project modules
from src.scripts.reset_database import reset_database
from src.scripts.load_initial_funds import main as load_initial_funds
from src.scripts.load_underlying_holdings import load_underlying_holdings
from src.scripts.verify_holdings import verify_holdings
from src.scripts.verify_fund_structure import verify_fund_structure
from src.scripts.verify_complete_structure import verify_complete_structure


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the complete FOFs-Capstone workflow")
    parser.add_argument("--reset-db", action="store_true", help="Reset the database before loading data")
    parser.add_argument("--skip-data-load", action="store_true", help="Skip data loading and just run the dashboard")
    parser.add_argument("--verify", action="store_true", help="Run verification scripts after data loading")
    return parser.parse_args()


async def run_workflow():
    """Run the complete workflow."""
    args = parse_args()
    
    print("\n" + "="*50)
    print("FOFs-Capstone Workflow Runner")
    print("="*50)
    
    # Step 1: Reset database (if requested)
    if args.reset_db:
        print("\n[1/4] Resetting database...")
        reset_database()
    
    # Step 2 & 3: Load data (unless skipped)
    if not args.skip_data_load:
        print("\n[2/4] Loading initial fund data...")
        await load_initial_funds()
        
        print("\n[3/4] Loading underlying holdings...")
        load_underlying_holdings()
        
        # Verification (if requested)
        if args.verify:
            print("\n[*] Verifying data...")
            verify_holdings()
            verify_fund_structure()
            verify_complete_structure()
    else:
        print("\n[*] Skipping data loading as requested...")
    
    # Step 4: Run dashboard
    print("\n[4/4] Starting dashboard...")
    dashboard_path = os.path.join(os.path.dirname(__file__), "run_dashboard.py")
    subprocess.run([sys.executable, dashboard_path])


if __name__ == "__main__":
    try:
        asyncio.run(run_workflow())
    except KeyboardInterrupt:
        print("\n\nWorkflow interrupted by user. Exiting...")
        sys.exit(0)
