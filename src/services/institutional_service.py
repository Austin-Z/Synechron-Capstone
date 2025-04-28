from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import pandas as pd
import streamlit as st
from fuzzywuzzy import fuzz, process
import json
import os
import pickle
from pathlib import Path

from src.models.institutional_holdings import Institute13F, InstitutionalHolding
from src.models.database import Fund, Filing, Holding

class InstitutionalService:
    """Service layer for institutional holdings-related database operations."""
    
    # Cache directory
    CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'cache')
    
    # Ensure cache directory exists
    @staticmethod
    def _ensure_cache_dir():
        """Ensure the cache directory exists."""
        if not os.path.exists(InstitutionalService.CACHE_DIR):
            os.makedirs(InstitutionalService.CACHE_DIR, exist_ok=True)
    
    @staticmethod
    def get_cache_path(fund_ticker: str, institution_id: int) -> str:
        """Get the cache file path for a fund-institution comparison."""
        InstitutionalService._ensure_cache_dir()
        return os.path.join(InstitutionalService.CACHE_DIR, f"{fund_ticker}_{institution_id}_comparison.pkl")
    
    @staticmethod
    def save_comparison_to_cache(fund_ticker: str, institution_id: int, comparison_data: Dict[str, Any]) -> bool:
        """Save comparison results to cache.
        
        Args:
            fund_ticker: The fund ticker
            institution_id: The institution ID
            comparison_data: The comparison data to cache
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add timestamp
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'data': comparison_data
            }
            
            # Save to cache file
            cache_path = InstitutionalService.get_cache_path(fund_ticker, institution_id)
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
            
            return True
        except Exception as e:
            print(f"Error saving comparison to cache: {str(e)}")
            return False
    
    @staticmethod
    def load_comparison_from_cache(fund_ticker: str, institution_id: int, max_age_days: int = 7) -> Optional[Dict[str, Any]]:
        """Load comparison results from cache if available and not too old.
        
        Args:
            fund_ticker: The fund ticker
            institution_id: The institution ID
            max_age_days: Maximum age of cache in days
            
        Returns:
            Optional[Dict]: The cached comparison data or None if not available or too old
        """
        try:
            cache_path = InstitutionalService.get_cache_path(fund_ticker, institution_id)
            
            # Check if cache file exists
            if not os.path.exists(cache_path):
                return None
            
            # Load cache data
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Check if cache is too old
            timestamp = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - timestamp > timedelta(days=max_age_days):
                return None
            
            return cache_data['data']
        except Exception as e:
            print(f"Error loading comparison from cache: {str(e)}")
            return None
    
    @staticmethod
    def get_institution_by_id(session: Session, institution_id: int) -> Optional[Institute13F]:
        """Get an institution by its ID."""
        return session.query(Institute13F).filter(Institute13F.id == institution_id).first()
    
    @staticmethod
    def get_institution_by_name(session: Session, name: str) -> Optional[Institute13F]:
        """Get an institution by its name."""
        # Try exact match first
        institution = session.query(Institute13F).filter(Institute13F.institution_name == name).first()
        if institution:
            return institution
        
        # If no exact match, try case-insensitive match
        institution = session.query(Institute13F).filter(func.lower(Institute13F.institution_name) == name.lower()).first()
        return institution
    
    @staticmethod
    def get_all_institutions(session: Session) -> List[Dict]:
        """Get all institutions with their metadata."""
        try:
            institutions = []
            for institution in session.query(Institute13F).all():
                # Get holdings count
                holdings_count = session.query(InstitutionalHolding).filter(
                    InstitutionalHolding.report_id == institution.id
                ).count()
                
                institutions.append({
                    'id': institution.id,
                    'name': institution.institution_name,
                    'report_date': institution.report_date,
                    'holdings_count': holdings_count
                })
            
            return sorted(institutions, key=lambda x: x['name'] if x['name'] else '')
        except Exception as e:
            print(f"Error getting institutions: {str(e)}")
            return []
    
    @staticmethod
    def get_institution_holdings(session: Session, institution_id: int) -> pd.DataFrame:
        """Get the holdings for an institution by ID."""
        try:
            # Query the holdings directly
            holdings = session.query(InstitutionalHolding).filter(
                InstitutionalHolding.report_id == institution_id
            ).all()
            
            if not holdings:
                return pd.DataFrame()
            
            # Convert to DataFrame format
            holdings_data = []
            for holding in holdings:
                holdings_data.append({
                    'Name': holding.issuer_name,
                    'Ticker': holding.ticker,
                    'Cusip': holding.cusip,
                    'Value': f"${holding.value:,.2f}" if holding.value else "$0.00",
                    'Value_Numeric': holding.value if holding.value else 0,
                    'Shares': holding.shares,
                    'Pct': holding.percentage if holding.percentage else 0,
                    'Security_Class': holding.security_class
                })
            
            return pd.DataFrame(holdings_data)
        except Exception as e:
            st.error(f"Error getting institution holdings: {str(e)}")
            return pd.DataFrame()
    
    @staticmethod
    def match_securities(fund_holdings: pd.DataFrame, institution_holdings: pd.DataFrame, 
                       name_match_threshold: int = 80) -> Tuple[pd.DataFrame, float, float]:
        """Match securities between fund holdings and institutional holdings using fuzzy matching.
        Optimized for performance with large datasets.
        """
        if fund_holdings.empty or institution_holdings.empty:
            return pd.DataFrame(), 0.0, 0.0
        
        # Initialize results
        matched_holdings = []
        matched_fund_values = 0.0
        
        # Ensure Value_Numeric column exists in both DataFrames
        if 'Value_Numeric' not in fund_holdings.columns and 'Value' in fund_holdings.columns:
            try:
                # Try to convert Value column to numeric
                fund_holdings['Value_Numeric'] = fund_holdings['Value'].apply(
                    lambda x: float(str(x).replace('$', '').replace(',', '')) if pd.notna(x) else 0.0
                )
            except Exception:
                # Fallback to zeros if conversion fails
                fund_holdings['Value_Numeric'] = 0.0
                
        if 'Value_Numeric' not in institution_holdings.columns and 'Value' in institution_holdings.columns:
            try:
                # Try to convert Value column to numeric
                institution_holdings['Value_Numeric'] = institution_holdings['Value'].apply(
                    lambda x: float(str(x).replace('$', '').replace(',', '')) if pd.notna(x) else 0.0
                )
            except Exception:
                # Fallback to zeros if conversion fails
                institution_holdings['Value_Numeric'] = 0.0
        
        # Calculate total fund value safely
        try:
            total_fund_value = fund_holdings['Value_Numeric'].sum()
        except Exception:
            total_fund_value = 0.0
            
        # Performance optimization: Convert DataFrames to dictionaries for faster lookups
        fund_dict = fund_holdings.to_dict('records')
        inst_dict = {}
        
        # Create ticker-based lookup for institutions - normalize tickers
        for record in institution_holdings.to_dict('records'):
            ticker = record.get('Ticker')
            if ticker and pd.notna(ticker):
                # Normalize ticker to handle different formats
                norm_ticker = str(ticker).upper().strip()
                if norm_ticker != 'NONE' and norm_ticker != 'NAN':
                    inst_dict[norm_ticker] = record
        
        # First pass: Match by ticker (much faster than iterating through DataFrames)
        ticker_matched_indices = set()
        for i, fund_record in enumerate(fund_dict):
            ticker = fund_record.get('Ticker')
            if ticker and pd.notna(ticker):
                # Normalize ticker
                norm_ticker = str(ticker).upper().strip()
                if norm_ticker != 'NONE' and norm_ticker != 'NAN' and norm_ticker in inst_dict:
                    inst_record = inst_dict[norm_ticker]
                    
                    # Safely get values with defaults
                    fund_value_numeric = fund_record.get('Value_Numeric', 0.0)
                    if not isinstance(fund_value_numeric, (int, float)) or pd.isna(fund_value_numeric):
                        fund_value_numeric = 0.0
                        
                    inst_value_numeric = inst_record.get('Value_Numeric', 0.0)
                    if not isinstance(inst_value_numeric, (int, float)) or pd.isna(inst_value_numeric):
                        inst_value_numeric = 0.0
                    
                    match_record = {
                        'Name': fund_record.get('Name', ''),
                        'Security': fund_record.get('Name', ''),  # For backward compatibility
                        'Ticker': ticker,
                        'Fund_Value': fund_record.get('Value', '$0.00'),
                        'Fund_Value_Numeric': fund_value_numeric,
                        'Fund_Pct': fund_record.get('Pct', 0.0),
                        'Institution_Value': inst_record.get('Value', '$0.00'),
                        'Institution_Value_Numeric': inst_value_numeric,
                        'Institution_Pct': inst_record.get('Pct', 0.0),
                        'Match_Type': 'Ticker'
                    }
                    
                    # Add parent fund info if available
                    if 'Parent_Fund' in fund_record:
                        match_record['Parent_Fund'] = fund_record['Parent_Fund']
                    if 'Parent_Ticker' in fund_record:
                        match_record['Parent_Ticker'] = fund_record['Parent_Ticker']
                    
                    matched_holdings.append(match_record)
                    matched_fund_values += fund_value_numeric
                    ticker_matched_indices.add(i)
        
        # Second pass: For non-ticker matches, use optimized name matching
        # Only process a limited number of potential matches to avoid performance issues
        MAX_NAME_MATCHES = 500  # Limit the number of name comparisons
        
        # Get unmatched fund records
        unmatched_fund_records = [rec for i, rec in enumerate(fund_dict) if i not in ticker_matched_indices]
        
        # Get institution names for matching
        inst_names = []
        for i, rec in enumerate(institution_holdings.to_dict('records')):
            name = rec.get('Name', '')
            if name and pd.notna(name):
                inst_names.append((i, str(name).strip()))
        
        # Limit to prevent performance issues
        inst_names = inst_names[:MAX_NAME_MATCHES]
        
        # Process only a subset of unmatched records if there are too many
        if len(unmatched_fund_records) > MAX_NAME_MATCHES:
            try:
                unmatched_fund_records = sorted(unmatched_fund_records, 
                                               key=lambda x: x.get('Value_Numeric', 0), 
                                               reverse=True)[:MAX_NAME_MATCHES]
            except Exception:
                # If sorting fails, just take the first MAX_NAME_MATCHES records
                unmatched_fund_records = unmatched_fund_records[:MAX_NAME_MATCHES]
        
        # Fuzzy match by name (with performance limits)
        for fund_record in unmatched_fund_records:
            fund_name = fund_record.get('Name', '')
            if not fund_name or not pd.notna(fund_name):
                continue
                
            fund_name = str(fund_name).strip()
            if not fund_name:
                continue
                
            # Find best match
            best_match = None
            best_score = name_match_threshold  # Only consider matches above threshold
            
            for inst_idx, inst_name in inst_names:
                if not inst_name:
                    continue
                    
                # Quick pre-check to avoid expensive fuzzy matching
                # If first characters don't match, likely a poor match
                if fund_name and inst_name and fund_name[0].lower() != inst_name[0].lower():
                    continue
                    
                score = fuzz.ratio(fund_name.lower(), inst_name.lower())
                if score > best_score:
                    best_score = score
                    best_match = (inst_idx, score)
            
            if best_match:
                inst_idx, score = best_match
                inst_record = institution_holdings.iloc[inst_idx].to_dict()
                
                match_record = {
                    'Name': fund_name,
                    'Security': fund_name,
                    'Ticker': fund_record.get('Ticker'),
                    'Fund_Value': fund_record.get('Value', '$0.00'),
                    'Fund_Value_Numeric': fund_record.get('Value_Numeric', 0.0),
                    'Fund_Pct': fund_record.get('Pct', 0.0),
                    'Institution_Value': inst_record.get('Value', '$0.00'),
                    'Institution_Value_Numeric': inst_record.get('Value_Numeric', 0.0),
                    'Institution_Pct': inst_record.get('Pct', 0.0),
                    'Match_Type': f'Name ({score}%)'
                }
                
                # Add parent fund info if available
                if 'Parent_Fund' in fund_record:
                    match_record['Parent_Fund'] = fund_record['Parent_Fund']
                if 'Parent_Ticker' in fund_record:
                    match_record['Parent_Ticker'] = fund_record['Parent_Ticker']
                
                matched_holdings.append(match_record)
                matched_fund_values += fund_record.get('Value_Numeric', 0.0)
        
        # Calculate percentages
        matched_pct_by_count = (len(matched_holdings) / len(fund_holdings)) * 100 if len(fund_holdings) > 0 else 0
        matched_pct_by_value = (matched_fund_values / total_fund_value) * 100 if total_fund_value > 0 else 0
        
        return pd.DataFrame(matched_holdings), matched_pct_by_count, matched_pct_by_value
    
    @staticmethod
    def compare_fund_with_institution(session: Session, fund_ticker: str, institution_id: int, 
                                     match_threshold: int = 80) -> Dict:
        """Compare a fund's holdings with an institution's holdings."""
        from src.services.fund_service import FundService
        
        # Get fund and institution data
        fund = FundService.get_fund_by_ticker(session, fund_ticker)
        institution = InstitutionalService.get_institution_by_id(session, institution_id)
        
        if not fund:
            return {"error": f"Fund with ticker {fund_ticker} not found"}
        
        if not institution:
            return {"error": f"Institution with ID {institution_id} not found"}
        
        # Get holdings
        fund_holdings = FundService.get_holdings_details(session, fund_ticker)
        institution_holdings = InstitutionalService.get_institution_holdings(session, institution_id)
        
        if fund_holdings.empty:
            return {"error": f"No holdings found for fund {fund_ticker}"}
        
        if institution_holdings.empty:
            return {"error": f"No holdings found for institution {institution_id}"}
        
        # Match securities
        matched_holdings, pct_by_count, pct_by_value = InstitutionalService.match_securities(
            fund_holdings, institution_holdings, match_threshold
        )
        
        # Prepare result
        result = {
            "fund": {
                "ticker": fund.ticker,
                "name": fund.name,
                "holdings_count": len(fund_holdings)
            },
            "institution": {
                "id": institution.id,
                "name": institution.institution_name,
                "report_date": institution.report_date.strftime("%Y-%m-%d") if institution.report_date else None,
                "holdings_count": len(institution_holdings)
            },
            "comparison": {
                "matched_count": len(matched_holdings),
                "matched_pct_by_count": pct_by_count,
                "matched_pct_by_value": pct_by_value,
                "matched_holdings": matched_holdings
            }
        }
        
        return result
