from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from src.models.database import Fund, Filing, Holding, FundRelationship
import pandas as pd
import streamlit as st
from sqlalchemy import func

class FundService:
    """Service layer for fund-related database operations."""
    
    def __init__(self):
        print("Available methods:", [method for method in dir(FundService) if not method.startswith('_')])
    
    @staticmethod
    def create_fund(session: Session, ticker: str, name: str, fund_type: str) -> Fund:
        fund = Fund(ticker=ticker, name=name, fund_type=fund_type)
        session.add(fund)
        session.commit()
        return fund
        
    @staticmethod
    def get_fund_by_ticker(session: Session, ticker: str) -> Optional[Fund]:
        return session.query(Fund).filter(Fund.ticker == ticker).first()
        
    @staticmethod
    def get_fund_holdings(session: Session, ticker: str) -> List[Holding]:
        fund = FundService.get_fund_by_ticker(session, ticker)
        if not fund or not fund.filings:
            return []
        latest_filing = fund.filings[0]  # Assuming ordered by date
        return latest_filing.holdings
        
    @staticmethod
    def create_filing(session: Session, 
                     fund: Fund, 
                     filing_date: datetime,
                     period_end_date: datetime,
                     total_assets: float) -> Filing:
        """Create a new filing record."""
        filing = Filing(
            fund_id=fund.id,
            filing_date=filing_date,
            period_end_date=period_end_date,
            total_assets=total_assets
        )
        session.add(filing)
        session.commit()
        return filing
        
    @staticmethod
    def create_holdings(session: Session, filing: Filing, holdings_df: pd.DataFrame) -> List[Holding]:
        """Create holdings records from a DataFrame."""
        import logging
        logger = logging.getLogger('fund_service')
        
        # Log the DataFrame info for debugging
        logger.info(f"Creating holdings for filing {filing.id} with {len(holdings_df)} rows")
        logger.info(f"DataFrame columns: {holdings_df.columns.tolist()}")
        
        if len(holdings_df) > 0:
            logger.info(f"Sample row: {holdings_df.iloc[0].to_dict()}")
        
        holdings = []
        try:
            for idx, row in holdings_df.iterrows():
                try:
                    # Clean value - remove $ and , then convert to float
                    value_raw = row.get('Value', 0)
                    if isinstance(value_raw, str):
                        value_str = value_raw.replace('$', '').replace(',', '')
                        value = float(value_str) if value_str else 0.0
                    else:
                        value = float(value_raw) if not pd.isna(value_raw) else 0.0
                    
                    # Clean percentage - already numeric in your data
                    pct_raw = row.get('Pct', 0)
                    pct = float(pct_raw) if not pd.isna(pct_raw) else 0.0
                    
                    # Handle NaN values for all fields
                    cusip = row.get('Cusip')
                    cusip = None if pd.isna(cusip) else str(cusip)
                    
                    ticker = row.get('Ticker')
                    ticker = None if pd.isna(ticker) else str(ticker)
                    
                    name = row.get('Name')
                    name = None if pd.isna(name) else str(name)
                    
                    title = row.get('Title')
                    title = None if pd.isna(title) else str(title)
                    
                    asset_type = row.get('Category')
                    asset_type = None if pd.isna(asset_type) else str(asset_type)
                    
                    holding = Holding(
                        filing_id=filing.id,
                        cusip=cusip,
                        ticker=ticker,
                        name=name,
                        title=title,
                        value=value,
                        percentage=pct,
                        asset_type=asset_type
                    )
                    holdings.append(holding)
                    
                except Exception as e:
                    logger.error(f"Error processing row {idx}: {str(e)}")
                    logger.error(f"Row data: {row.to_dict()}")
            
            # Only commit if we have holdings to save
            if holdings:
                logger.info(f"Saving {len(holdings)} holdings to database")
                session.bulk_save_objects(holdings)
                session.commit()
                logger.info(f"Successfully saved {len(holdings)} holdings")
            else:
                logger.warning("No holdings to save")
                
        except Exception as e:
            logger.error(f"Error creating holdings: {str(e)}")
            session.rollback()
            
        return holdings
        
    @staticmethod
    def create_fund_relationship(session: Session,
                               filing: Filing,
                               parent_fund: Fund,
                               child_ticker: str,
                               percentage: float,
                               value: float) -> Optional[FundRelationship]:
        """Create a fund relationship record."""
        child_fund = session.query(Fund).filter(Fund.ticker == child_ticker).first()
        if not child_fund:
            return None
            
        relationship = FundRelationship(
            parent_fund_id=parent_fund.id,
            child_fund_id=child_fund.id,
            filing_id=filing.id,
            percentage=percentage,
            value=value
        )
        session.add(relationship)
        session.commit()
        return relationship
        
    @staticmethod
    def get_sankey_data(session: Session, ticker: str) -> Dict:
        """Get Sankey diagram data for fund relationships."""
        fund = session.query(Fund).filter(Fund.ticker == ticker).first()
        if not fund or not fund.filings:
            return None
        
        latest_filing = fund.filings[0]
        
        # Get fund relationships
        relationships = session.query(FundRelationship).filter(
            FundRelationship.filing_id == latest_filing.id
        ).all()
        
        # Prepare Sankey data
        nodes = []
        links = []
        node_map = {fund.id: 0}  # Parent fund is always first
        nodes.append({"name": fund.ticker, "value": latest_filing.total_assets})
        
        for rel in relationships:
            # Add child fund if not already added
            if rel.child_fund_id not in node_map:
                node_map[rel.child_fund_id] = len(nodes)
                child_fund = session.query(Fund).get(rel.child_fund_id)
                nodes.append({"name": child_fund.ticker, "value": rel.value})
            
            # Add link
            links.append({
                "source": node_map[rel.parent_fund_id],
                "target": node_map[rel.child_fund_id],
                "value": rel.value,
                "percentage": rel.percentage
            })
        
        return {
            "nodes": nodes,
            "links": links
        }

    @staticmethod
    def get_asset_allocation(holdings: List[Holding]) -> Dict[str, float]:
        """Get asset allocation breakdown."""
        allocation = {}
        total_value = sum(h.value for h in holdings)
        
        for holding in holdings:
            asset_type = holding.asset_type or "Other"
            allocation[asset_type] = allocation.get(asset_type, 0) + (holding.value / total_value * 100)
        
        return dict(sorted(allocation.items(), key=lambda x: x[1], reverse=True))

    @staticmethod
    def get_top_holdings(holdings: List[Holding], limit: int = 10) -> List[Dict]:
        """Get top holdings by value."""
        sorted_holdings = sorted(holdings, key=lambda x: x.value, reverse=True)
        return [
            {
                "Name": h.name,
                "Ticker": h.ticker,
                "Value": h.value,
                "Percentage": h.percentage,
                "Type": h.asset_type
            }
            for h in sorted_holdings[:limit]
        ]

    @staticmethod
    def get_holdings_by_fund(session: Session, fund_id: int) -> List[Dict]:
        """Get holdings for a specific fund with their details."""
        fund = session.query(Fund).get(fund_id)
        if not fund or not fund.filings:
            return []
        
        latest_filing = fund.filings[0]
        return FundService.get_top_holdings(latest_filing.holdings)

    @staticmethod
    def create_or_update_fund(session: Session, ticker: str, name: str, fund_type: str) -> Fund:
        """Create or update a fund record."""
        fund = session.query(Fund).filter(Fund.ticker == ticker).first()
        
        if not fund:
            fund = Fund(ticker=ticker, name=name, fund_type=fund_type)
            session.add(fund)
        else:
            fund.name = name
            fund.fund_type = fund_type
            fund.updated_at = datetime.utcnow()
        
        session.commit()
        return fund 

    @staticmethod
    def get_holdings_details(session: Session, ticker: str) -> pd.DataFrame:
        """Get holdings details for a fund."""
        try:
            fund = FundService.get_fund_by_ticker(session, ticker)
            if not fund or not fund.filings:
                st.warning(f"No fund or filings found for {ticker}")
                return pd.DataFrame()
            
            # First try to find a filing with holdings
            filing_with_holdings = None
            
            # Sort filings by date to ensure we try the latest ones first
            sorted_filings = sorted(fund.filings, key=lambda x: x.filing_date, reverse=True)
            
            # Try to find a filing with holdings
            for filing in sorted_filings:
                if filing.holdings:
                    filing_with_holdings = filing
                    break
            
            # If no filing with holdings found, use the latest filing
            if not filing_with_holdings and sorted_filings:
                filing_with_holdings = sorted_filings[0]
                
            # If still no filing found, return empty DataFrame
            if not filing_with_holdings:
                return pd.DataFrame()
            
            holdings_data = []
            
            for holding in filing_with_holdings.holdings:
                holdings_data.append({
                    'Name': holding.name,
                    'Ticker': holding.ticker,
                    'Cusip': holding.cusip,
                    'Value': f"${holding.value:,.2f}",
                    'Pct': holding.percentage,
                    'Category': holding.asset_type
                })
            
            return pd.DataFrame(holdings_data)
        
        except Exception as e:
            st.error(f"Error getting holdings for {ticker}: {str(e)}")
            return pd.DataFrame()

    @staticmethod
    def update_fund_holdings(session: Session, ticker: str, holdings_df: pd.DataFrame) -> bool:
        """Update a fund's holdings with new data."""
        try:
            fund = session.query(Fund).filter(Fund.ticker == ticker).first()
            if not fund:
                return False
            
            # Create new filing
            filing = Filing(
                fund_id=fund.id,
                filing_date=datetime.utcnow(),
                period_end_date=datetime.utcnow(),
                total_assets=holdings_df['Value'].sum() if 'Value' in holdings_df.columns else 0
            )
            session.add(filing)
            
            # Delete old relationships for this fund
            session.query(FundRelationship).filter(
                FundRelationship.parent_fund_id == fund.id
            ).delete()
            
            # Create new holdings
            holdings = []
            for _, row in holdings_df.iterrows():
                value_str = str(row.get('Value', '0')).replace('$', '').replace(',', '')
                value = float(value_str) if value_str else 0.0
                pct = float(row.get('Pct', 0))
                
                holding = Holding(
                    filing_id=filing.id,
                    cusip=row.get('Cusip'),
                    ticker=row.get('Ticker', 'None'),
                    name=row.get('Name'),
                    title=row.get('Title'),
                    value=value,
                    percentage=pct,
                    asset_type=row.get('Category')
                )
                holdings.append(holding)
            
            session.bulk_save_objects(holdings)
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            raise e 

    @staticmethod
    def update_holding_ticker(session: Session, cusip: str, ticker: str) -> bool:
        """Update the ticker for a holding with given CUSIP."""
        try:
            holdings = session.query(Holding).filter(Holding.cusip == cusip).all()
            for holding in holdings:
                holding.ticker = ticker
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            return False 

    @staticmethod
    def get_all_fund_tickers(session: Session) -> list[str]:
        """Get list of all available fund tickers"""
        try:
            # Query distinct tickers from the Fund table
            funds = session.query(Fund.ticker).distinct().all()
            # Convert list of tuples to list of strings
            return [fund[0] for fund in funds if fund[0]]  # Filter out None values
        except Exception as e:
            print(f"Error getting fund tickers: {str(e)}")
            return [] 

    @staticmethod
    def get_top_level_funds(session: Session) -> List[str]:
        """Get list of top-level (parent) fund tickers"""
        try:
            # Query funds that are parents (have holdings_as_parent) but not children
            parent_funds = session.query(Fund.ticker).filter(
                Fund.holdings_as_parent.any() &  # Has child funds
                ~Fund.holdings_as_child.any()    # Is not a child fund
            ).all()
            return [fund[0] for fund in parent_funds if fund[0]]
        except Exception as e:
            print(f"Error getting top level funds: {str(e)}")
            return [] 

    @staticmethod
    def get_funds_with_metadata(session: Session) -> List[Dict]:
        """Get all funds with their metadata"""
        try:
            funds = []
            for fund in session.query(Fund).all():
                is_parent = bool(fund.holdings_as_parent)
                funds.append({
                    'ticker': fund.ticker,
                    'name': fund.name,
                    'is_parent': is_parent,
                    'holdings_count': len(fund.filings[0].holdings) if fund.filings else 0
                })
            return funds
        except Exception as e:
            print(f"Error getting funds with metadata: {str(e)}")
            return [] 

    @staticmethod
    def get_all_mutual_funds(session: Session) -> List[Dict]:
        """Get all mutual funds with their holdings"""
        try:
            funds = []
            # Get all funds first
            all_funds = session.query(Fund).all()
            
            for fund in all_funds:
                # Include all funds, but calculate holdings count if available
                holdings_count = 0
                if fund.filings and len(fund.filings) > 0:
                    latest_filing = fund.filings[0]  # Assuming ordered by date desc
                    holdings_count = len(latest_filing.holdings)
                
                # Include the fund regardless of whether it has holdings
                funds.append({
                    'ticker': fund.ticker,
                    'name': fund.name,
                    'holdings_count': holdings_count
                })
            
            return sorted(funds, key=lambda x: x['ticker'])
            
        except Exception as e:
            print(f"Error getting mutual funds: {str(e)}")
            st.error(f"Database error: {str(e)}")  # Show error in UI
            return [] 

    @staticmethod
    def get_funds_by_type(session, fund_type: str):
        """Get all funds of a specific type"""
        return session.query(Fund).filter(Fund.fund_type == fund_type).all()
    
    @staticmethod
    def determine_fund_type(session, ticker: str) -> str:
        """Determine fund type based on holdings"""
        holdings = FundService.get_holdings_details(session, ticker)
        if holdings.empty:
            return 'underlying_fund'
        
        # If more than 50% of holdings are funds, it's a fund of funds
        fund_holdings = holdings[holdings['Category'].str.contains('Fund', na=False)]
        return 'fund_of_funds' if len(fund_holdings) > len(holdings) / 2 else 'underlying_fund' 

    @staticmethod
    def get_fund_by_name(session: Session, name: str) -> Optional[Fund]:
        """Get fund by name"""
        try:
            # Try exact match first
            fund = session.query(Fund).filter(Fund.name == name).first()
            if fund:
                return fund
            
            # If no exact match, try case-insensitive match
            fund = session.query(Fund).filter(func.lower(Fund.name) == name.lower()).first()
            return fund
            
        except Exception as e:
            print(f"Error getting fund by name: {str(e)}")
            return None 