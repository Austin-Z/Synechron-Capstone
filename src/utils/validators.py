from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime

class DataValidator:
    @staticmethod
    def validate_fund_data(data: Dict[str, Any]) -> Optional[str]:
        """Validate fund data before database insertion."""
        required_fields = ['ticker', 'name', 'fund_type']
        for field in required_fields:
            if field not in data or not data[field]:
                return f"Missing required field: {field}"
                
        if len(data['ticker']) > 10:
            return "Ticker length exceeds 10 characters"
            
        return None

    @staticmethod
    def validate_filing_data(data: Dict[str, Any]) -> Optional[str]:
        """Validate filing data before database insertion."""
        if not isinstance(data.get('filing_date'), datetime):
            return "Invalid filing_date format"
            
        if not isinstance(data.get('period_end_date'), datetime):
            return "Invalid period_end_date format"
            
        if data.get('total_assets') and not isinstance(data['total_assets'], (int, float)):
            return "Invalid total_assets format"
            
        return None

    @staticmethod
    def validate_holdings_df(df: pd.DataFrame) -> Optional[str]:
        """Validate holdings DataFrame before database insertion."""
        required_columns = ['Name', 'Value']
        for col in required_columns:
            if col not in df.columns:
                return f"Missing required column: {col}"
                
        if df['Value'].isnull().all():
            return "No valid values in Value column"
            
        return None 