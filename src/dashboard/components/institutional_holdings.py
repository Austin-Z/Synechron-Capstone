import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sqlalchemy.orm import Session
import os

from src.services.fund_service import FundService
from src.services.institutional_service import InstitutionalService
from src.models.institutional_holdings import Institute13F

class InstitutionalHoldingsAnalyzer:
    """Analyzer for comparing fund holdings with institutional holdings."""
    
    def __init__(self, session: Session, fund_ticker: str, institution_id: int = None):
        self.session = session
        self.fund_ticker = fund_ticker
        self.institution_id = institution_id
        
        # Initialize data
        self.fund = None
        self.institution = None
        self.fund_holdings = None
        self.underlying_securities = None  # New field for underlying securities
        self.institution_holdings = None
        self.matched_holdings = None
        self.comparison_metrics = None
        
        # Load data if institution_id is provided
        if institution_id:
            self._initialize_data()
    
    def _initialize_data(self):
        """Initialize fund and institution data."""
        # Check if we have a global cache for underlying securities
        if 'underlying_securities_cache' not in st.session_state:
            st.session_state.underlying_securities_cache = {}
            
        # Create a cache key for this fund
        fund_cache_key = f"underlying_{self.fund_ticker}"
        
        # Get fund data
        self.fund = FundService.get_fund_by_ticker(self.session, self.fund_ticker)
        if not self.fund:
            st.error(f"Fund with ticker {self.fund_ticker} not found")
            return
        
        # Get fund holdings
        self.fund_holdings = FundService.get_holdings_details(self.session, self.fund_ticker)
        if self.fund_holdings.empty:
            st.warning(f"No holdings found for fund {self.fund_ticker}")
            return
        
        # Add Value_Numeric column if it doesn't exist
        if 'Value_Numeric' not in self.fund_holdings.columns:
            self.fund_holdings['Value_Numeric'] = self.fund_holdings['Value'].str.replace('$', '').str.replace(',', '').astype(float)
        
        # Get underlying securities for fund-of-funds (use cache if available)
        if fund_cache_key in st.session_state.underlying_securities_cache:
            self.underlying_securities = st.session_state.underlying_securities_cache[fund_cache_key]
        else:
            # Show a spinner while loading underlying securities
            with st.spinner(f"Loading underlying securities for {self.fund_ticker}..."):
                self.underlying_securities = self._get_underlying_securities()
                # Cache the result
                st.session_state.underlying_securities_cache[fund_cache_key] = self.underlying_securities
        
        # Get institution data
        if self.institution_id:
            self.institution = InstitutionalService.get_institution_by_id(self.session, self.institution_id)
            if not self.institution:
                st.error(f"Institution with ID {self.institution_id} not found")
                return
            
            # Get institution holdings
            self.institution_holdings = InstitutionalService.get_institution_holdings(self.session, self.institution_id)
            if self.institution_holdings.empty:
                st.warning(f"No holdings found for institution {self.institution_id}")
                return
            
            # Match securities
            self._match_securities()
    
    def _get_underlying_securities(self):
        """Get all underlying securities for a fund-of-funds with performance optimizations."""
        # Extract all valid tickers from fund holdings
        valid_tickers = []
        ticker_to_fund_map = {}
        
        for _, holding in self.fund_holdings.iterrows():
            ticker = holding.get('Ticker')
            if ticker and str(ticker).upper() != 'NONE' and pd.notna(ticker):
                value_numeric = 0
                if 'Value_Numeric' in holding:
                    value_numeric = holding.get('Value_Numeric', 0)
                elif 'Value' in holding:
                    # Try to convert Value to numeric
                    try:
                        value_str = str(holding.get('Value', '0')).replace('$', '').replace(',', '')
                        value_numeric = float(value_str) if value_str else 0.0
                    except (ValueError, TypeError):
                        value_numeric = 0.0
                
                valid_tickers.append(ticker)
                ticker_to_fund_map[ticker] = {
                    'Name': holding.get('Name', ''),
                    'Value_Numeric': value_numeric
                }

        if not valid_tickers:
            return pd.DataFrame()

        # Performance optimization: Create a list to store DataFrames instead of concatenating in each iteration
        underlying_dfs = []

        # Process in smaller batches to avoid memory issues
        batch_size = 5  # Adjust based on performance testing
        for i in range(0, len(valid_tickers), batch_size):
            batch_tickers = valid_tickers[i:i+batch_size]

            # Process each ticker in the batch
            for ticker in batch_tickers:
                try:
                    # Get holdings of this underlying fund
                    underlying = FundService.get_holdings_details(self.session, ticker)
                    if not underlying.empty:
                        # Add Value_Numeric column if it doesn't exist
                        if 'Value_Numeric' not in underlying.columns and 'Value' in underlying.columns:
                            try:
                                # Try multiple methods to convert Value to numeric
                                if underlying['Value'].dtype == 'object':
                                    # If string values with $ and commas
                                    underlying['Value_Numeric'] = underlying['Value'].apply(
                                        lambda x: float(str(x).replace('$', '').replace(',', '')) if pd.notna(x) else 0.0
                                    )
                                else:
                                    # If already numeric but wrong column name
                                    underlying['Value_Numeric'] = underlying['Value']
                            except Exception as e:
                                st.warning(f"Error converting values for {ticker}: {str(e)}")
                                # Fallback if the conversion fails
                                underlying['Value_Numeric'] = 0.0

                        # Add parent fund info
                        underlying['Parent_Fund'] = ticker_to_fund_map[ticker]['Name']
                        underlying['Parent_Ticker'] = ticker

                        # Ensure all required columns exist
                        for col in ['Name', 'Ticker', 'Cusip', 'Value', 'Value_Numeric', 'Pct', 'Category']:
                            if col not in underlying.columns:
                                underlying[col] = None

                        # Add to list of DataFrames
                        underlying_dfs.append(underlying)
                except Exception as e:
                    st.warning(f"Error processing underlying fund {ticker}: {str(e)}")
                    continue
        
        # Combine all DataFrames at once (more efficient than repeated concatenation)
        if underlying_dfs:
            try:
                result = pd.concat(underlying_dfs, ignore_index=True)
                # Final check to ensure Value_Numeric is properly set
                if 'Value_Numeric' in result.columns:
                    result['Value_Numeric'] = result['Value_Numeric'].apply(
                        lambda x: float(x) if pd.notna(x) and not isinstance(x, str) else 
                                  (float(str(x).replace('$', '').replace(',', '')) if pd.notna(x) and isinstance(x, str) else 0.0)
                    )
                return result
            except Exception as e:
                st.error(f"Error combining underlying securities: {str(e)}")
                return pd.DataFrame()
        else:
            return pd.DataFrame()
    
    def _match_securities(self):
        """Match securities between underlying fund holdings and institutional holdings."""
        if self.underlying_securities is None or self.underlying_securities.empty or self.institution_holdings is None:
            # If no underlying securities, fall back to direct holdings
            if self.fund_holdings is not None and not self.fund_holdings.empty:
                matched_holdings, pct_by_count, pct_by_value = InstitutionalService.match_securities(
                    self.fund_holdings, self.institution_holdings, 80
                )
                
                self.matched_holdings = matched_holdings
                self.comparison_metrics = {
                    "matched_count": len(matched_holdings),
                    "total_fund_holdings": len(self.fund_holdings),
                    "total_institution_holdings": len(self.institution_holdings),
                    "matched_pct_by_count": pct_by_count,
                    "matched_pct_by_value": pct_by_value,
                    "using_underlying": False
                }
            return
        
        # Use a fixed threshold of 80 for name matching with underlying securities
        matched_holdings, pct_by_count, pct_by_value = InstitutionalService.match_securities(
            self.underlying_securities, self.institution_holdings, 80
        )
        
        self.matched_holdings = matched_holdings
        self.comparison_metrics = {
            "matched_count": len(matched_holdings),
            "total_fund_holdings": len(self.underlying_securities),
            "total_institution_holdings": len(self.institution_holdings),
            "matched_pct_by_count": pct_by_count,
            "matched_pct_by_value": pct_by_value,
            "using_underlying": True
        }
    
    def set_institution(self, institution_id: int, force_refresh: bool = False):
        """Set the institution to compare with and reload data.
        
        Args:
            institution_id: The institution ID to compare with
            force_refresh: If True, ignore cache and force recalculation
        """
        # If the institution ID hasn't changed and we're not forcing a refresh, do nothing
        if self.institution_id == institution_id and not force_refresh:
            return
            
        self.institution_id = institution_id
        
        # Try to load from cache first (if not forcing refresh)
        if not force_refresh:
            cached_data = InstitutionalService.load_comparison_from_cache(self.fund_ticker, institution_id)
            if cached_data:
                # Use cached data
                self.institution = cached_data.get('institution')
                self.institution_holdings = cached_data.get('institution_holdings')
                self.matched_holdings = cached_data.get('matched_holdings')
                self.comparison_metrics = cached_data.get('comparison_metrics')
                self.underlying_securities = cached_data.get('underlying_securities')
                return
        
        # If no cache, cache is invalid, or force_refresh, initialize data
        self._initialize_data()
        
        # Save to cache for future use
        if self.institution and self.matched_holdings is not None:
            cache_data = {
                'institution': self.institution,
                'institution_holdings': self.institution_holdings,
                'matched_holdings': self.matched_holdings,
                'comparison_metrics': self.comparison_metrics,
                'underlying_securities': self.underlying_securities
            }
            InstitutionalService.save_comparison_to_cache(self.fund_ticker, institution_id, cache_data)
    
    def render_comparison_metrics(self):
        """Render comparison metrics."""
        if not self.comparison_metrics:
            st.warning("No comparison metrics available. Please select an institution to compare with.")
            return
        
        # Determine if we're using underlying securities
        using_underlying = self.comparison_metrics.get('using_underlying', False)
        holdings_type = "Underlying Securities" if using_underlying else "Direct Holdings"
        
        # Create metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                f"Overlapping {holdings_type}", 
                f"{self.comparison_metrics['matched_count']} / {self.comparison_metrics['total_fund_holdings']}",
                help=f"Number of fund {holdings_type.lower()} that match with the institution's holdings"
            )
        
        with col2:
            st.metric(
                "Overlap by Count", 
                f"{self.comparison_metrics['matched_pct_by_count']:.1f}%",
                help="Percentage of fund holdings that match with the institution's holdings by count"
            )
        
        with col3:
            st.metric(
                "Overlap by Value", 
                f"{self.comparison_metrics['matched_pct_by_value']:.1f}%",
                help="Percentage of fund holdings that match with the institution's holdings by value"
            )
    
    def render_holdings_comparison_table(self):
        """Render a table comparing fund holdings with institution holdings."""
        if self.matched_holdings is None or self.matched_holdings.empty:
            st.info("No matching holdings found.")
            return
        
        
        # Determine if we're using underlying securities
        using_underlying = self.comparison_metrics.get('using_underlying', False)
        holdings_type = "Underlying Securities" if using_underlying else "Direct Holdings"
        
        st.subheader(f"Matching {holdings_type}")
        
        # Prepare data for display
        display_data = []
        for _, row in self.matched_holdings.iterrows():
            # Create a dictionary with available columns
            entry = {}
            
            # Add security name - check for both 'Name' and 'Security' columns
            if 'Name' in row:
                entry["Security Name"] = row["Name"]
            elif 'Security' in row:
                entry["Security Name"] = row["Security"]
            else:
                entry["Security Name"] = "Unknown"
                
            # Add ticker if available
            if 'Ticker' in row:
                entry["Ticker"] = row["Ticker"] if pd.notna(row["Ticker"]) else ""
            
            # Add parent fund if available and using underlying securities
            if using_underlying and 'Parent_Fund' in row:
                entry["Parent Fund"] = row["Parent_Fund"]
            
            # Add fund value
            if 'Fund_Value' in row:
                entry["Fund Value"] = row["Fund_Value"]
            
            # Add institution value
            if 'Institution_Value' in row:
                entry["Institution Value"] = row["Institution_Value"]
            
            # Add fund percentage
            if 'Fund_Pct' in row:
                entry["Fund %"] = f"{row['Fund_Pct']:.2f}%" if pd.notna(row['Fund_Pct']) else ""
            
            # Add institution percentage
            if 'Institution_Pct' in row:
                entry["Institution %"] = f"{row['Institution_Pct']:.2f}%" if pd.notna(row['Institution_Pct']) else ""
            
            display_data.append(entry)
        
        # Create DataFrame and display
        df = pd.DataFrame(display_data)
        
        # Only show Parent Fund column if using underlying securities
        columns_to_display = df.columns.tolist()
        if not using_underlying and "Parent Fund" in columns_to_display:
            columns_to_display.remove("Parent Fund")
        
        st.dataframe(df[columns_to_display], use_container_width=True)
    
    def render_holdings_chart(self):
        """Render a chart comparing fund holdings with institution holdings."""
        if self.matched_holdings is None or self.matched_holdings.empty:
            return
        
        # Determine if we're using underlying securities
        using_underlying = self.comparison_metrics.get('using_underlying', False)
        holdings_type = "Underlying Securities" if using_underlying else "Direct Holdings"
        
        st.subheader(f"{holdings_type} Comparison Chart")
        
        # Check if we have the necessary columns for the chart
        required_columns = ['Fund_Value']
        if not all(col in self.matched_holdings.columns for col in required_columns):
            st.warning(f"Cannot create chart: missing required columns. Available columns: {self.matched_holdings.columns.tolist()}")
            return
        
        # Prepare data for chart
        try:
            # Create a copy of the DataFrame to avoid modifying the original
            chart_data = self.matched_holdings.copy()
            
            # Ensure we have a name column (could be 'Name' or 'Security')
            if 'Name' not in chart_data.columns and 'Security' in chart_data.columns:
                chart_data['Name'] = chart_data['Security']
            elif 'Name' not in chart_data.columns:
                # If neither column exists, create a placeholder
                chart_data['Name'] = [f"Security {i+1}" for i in range(len(chart_data))]
            
            # Ensure we have numeric columns for sorting and plotting
            if 'Fund_Value_Numeric' in chart_data.columns:
                # Use Fund_Value_Numeric for sorting
                top_holdings = chart_data.nlargest(10, 'Fund_Value_Numeric')
            elif 'Fund_Value' in chart_data.columns:
                # Try to convert Fund_Value to numeric if it's not already
                try:
                    if chart_data['Fund_Value'].dtype == 'object':
                        # If it's a string with $ and commas, convert it
                        chart_data['Fund_Value_Numeric'] = chart_data['Fund_Value'].astype(str).str.replace('$', '').str.replace(',', '').astype(float)
                        top_holdings = chart_data.nlargest(10, 'Fund_Value_Numeric')
                    else:
                        top_holdings = chart_data.nlargest(10, 'Fund_Value')
                except Exception as e:
                    st.warning(f"Could not convert Fund_Value to numeric: {str(e)}")
                    # Just take the first 10 rows if we can't sort
                    top_holdings = chart_data.head(10)
            else:
                # Just take the first 10 rows if we don't have a value column
                top_holdings = chart_data.head(10)
            
            # Create figure
            fig = go.Figure()
            
            # Add fund holdings bar - use numeric column if available
            if 'Fund_Value_Numeric' in top_holdings.columns:
                fig.add_trace(go.Bar(
                    x=top_holdings['Name'],
                    y=top_holdings['Fund_Value_Numeric'],
                    name=f'{self.fund_ticker} {holdings_type}',
                    marker_color='#1f77b4'
                ))
            elif 'Fund_Value' in top_holdings.columns:
                fig.add_trace(go.Bar(
                    x=top_holdings['Name'],
                    y=top_holdings['Fund_Value'],
                    name=f'{self.fund_ticker} {holdings_type}',
                    marker_color='#1f77b4'
                ))
            
            # Add institution holdings bar if the column exists - use numeric column if available
            if 'Institution_Value_Numeric' in top_holdings.columns:
                fig.add_trace(go.Bar(
                    x=top_holdings['Name'],
                    y=top_holdings['Institution_Value_Numeric'],
                    name=f'{self.institution.institution_name if hasattr(self.institution, "institution_name") else "Institution"} Holdings',
                    marker_color='#ff7f0e'
                ))
            elif 'Institution_Value' in top_holdings.columns:
                fig.add_trace(go.Bar(
                    x=top_holdings['Name'],
                    y=top_holdings['Institution_Value'],
                    name=f'{self.institution.institution_name if hasattr(self.institution, "institution_name") else "Institution"} Holdings',
                    marker_color='#ff7f0e'
                ))
        except Exception as e:
            st.error(f"Error creating chart: {str(e)}")
            return
        
        # Update layout
        fig.update_layout(
            title=f'Top 10 Overlapping {holdings_type} by Value',
            xaxis_title='Security',
            yaxis_title='Value ($)',
            barmode='group',
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)


def render_institutional_holdings_analysis(session, fund_ticker, institution_id, force_refresh=False):
    """Render institutional holdings analysis dashboard.
    
    Args:
        session: Database session
        fund_ticker: Ticker of the fund to analyze
        institution_id: ID of the institution to compare with
        force_refresh: Whether to force refresh the data
    """
    # Create a key for the analyzer
    analyzer_key = f"institutional_analyzer_{fund_ticker}"
    
    # Initialize analyzer if needed
    if analyzer_key not in st.session_state:
        st.session_state[analyzer_key] = InstitutionalHoldingsAnalyzer(session, fund_ticker, institution_id)
    
    # Get the analyzer from session state
    analyzer = st.session_state[analyzer_key]
    
    # Update the analyzer with the selected institution if needed
    if analyzer.institution_id != institution_id or force_refresh:
        with st.spinner(f"{'Refreshing' if force_refresh else 'Loading'} comparison data..."):
            analyzer.set_institution(institution_id, force_refresh=force_refresh)
    
    # Show cache status silently (no UI message)
    cache_path = InstitutionalService.get_cache_path(fund_ticker, institution_id)
        
    # Render comparison results
    
    # Get the institution name
    institution_name = None
    if analyzer.institution:
        if hasattr(analyzer.institution, 'institution_name'):
            institution_name = analyzer.institution.institution_name
        elif isinstance(analyzer.institution, dict) and 'institution_name' in analyzer.institution:
            institution_name = analyzer.institution['institution_name']
    
    if institution_name:
        st.subheader(f"Comparison with {institution_name}")
    else:
        st.subheader("Institutional Comparison")
    
    # Add a clear explanation about fund-of-funds vs institutional holdings
    st.info("""
    **How This Comparison Works**: 
    For fund-of-funds like MDIZX that primarily hold other mutual funds, we analyze the underlying securities 
    held by those funds to provide a meaningful comparison with institutional investors' holdings.
    
    This two-level analysis reveals how the fund's ultimate exposure to individual securities compares with 
    what major institutions are holding directly.
    """)
    
    # Render metrics
    analyzer.render_comparison_metrics()
    
    # Render holdings comparison table
    analyzer.render_holdings_comparison_table()
    
    # Render holdings chart
    analyzer.render_holdings_chart()
