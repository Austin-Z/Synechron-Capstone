import streamlit as st
from collections import defaultdict
from datetime import datetime
from src.services.fund_service import FundService
import plotly.graph_objects as go
import pandas as pd
from sqlalchemy.orm import Session

class PortfolioAnalyzer:
    def __init__(self, session: Session, identifiers: list[str]):
        self.session = session
        self.identifiers = identifiers
        
        # Initialize both data structures
        self.holdings_map = {}  # For overlap analysis
        self.holdings_data = {}  # For visualization
        
        # Collect data for both uses
        self._initialize_holdings()
        
    def _initialize_holdings(self):
        """Initialize holdings data for both visualization and analysis"""
        # Create an expander for fund details
        with st.expander("📊 Fund Details", expanded=True):
            st.markdown("### Holdings Breakdown")
            
            # Create tabs for each fund
            fund_tabs = st.tabs(self.identifiers)
            
            for identifier, tab in zip(self.identifiers, fund_tabs):
                with tab:
                    # Try getting fund by ticker first
                    fund = FundService.get_fund_by_ticker(self.session, identifier)
                    if not fund:
                        # If not found by ticker, try by name
                        fund = FundService.get_fund_by_name(self.session, identifier)
                    
                    fund_name = fund.name if fund else "Name not available"
                    
                    # Display identifier and full name
                    st.markdown(f"#### {identifier}")
                    st.markdown(f"*{fund_name}*")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        df = FundService.get_holdings_details(self.session, identifier)
                        st.metric("Number of Holdings", len(df) if not df.empty else 0)
                    
                    with col2:
                        if not df.empty:
                            st.metric("Total Value", df['Value'].iloc[0] if 'Value' in df.columns else "$0")
                    
                    if not df.empty:
                        st.markdown("##### Top Holdings")
                        st.dataframe(
                            df.head(),
                            use_container_width=True
                        )
                        if 'Value' in df.columns:
                            df['Value_Numeric'] = df['Value'].str.replace('$', '').str.replace(',', '').astype(float)
                        
                        # Store data for both uses
                        self.holdings_data[identifier] = df
                        self.holdings_map[identifier] = {
                            row['Name']: row for _, row in df.iterrows()
                        }
                    else:
                        self.holdings_data[identifier] = pd.DataFrame()
                        self.holdings_map[identifier] = {}

    def analyze_overlaps(self, show_summary=True):
        """Analyze overlapping holdings across funds"""
        overlaps = defaultdict(lambda: {'funds': set(), 'total_value': 0})
        
        # Convert holdings_map to DataFrames if needed
        holdings_data = {}
        for identifier, holdings in self.holdings_map.items():
            if isinstance(holdings, dict) and holdings:
                holdings_data[identifier] = holdings
        
        if show_summary:
            with st.expander("📈 Analysis Summary", expanded=True):
                st.markdown("### Holdings by Fund")
                cols = st.columns(len(self.identifiers))
                for fund, col in zip(self.identifiers, cols):
                    with col:
                        holdings = holdings_data.get(fund, {})
                        st.metric(f"{fund}", len(holdings), "Holdings")
        
        # Process overlaps
        for fund, holdings in holdings_data.items():
            for name, holding in holdings.items():
                stock_name = holding['Name']
                # Convert value string to numeric
                value_str = holding.get('Value', '0')
                if isinstance(value_str, str):
                    value_str = value_str.replace('$', '').replace(',', '')
                try:
                    value = float(value_str)
                except (ValueError, TypeError):
                    value = 0
                
                overlaps[stock_name]['funds'].add(fund)
                overlaps[stock_name]['total_value'] += value
        
        if show_summary:
            # Portfolio metrics
            st.markdown("### Portfolio Overview")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Unique Holdings", len(overlaps))
            with col2:
                st.metric("Overlapping Holdings", len([h for h in overlaps.values() if len(h['funds']) > 1]))
            with col3:
                st.metric(
                    "Max Holdings Overlap", 
                    max((len(h['funds']) for h in overlaps.values()), default=0),
                    help="The highest number of funds that hold the same security. With your current selection of "
                         f"{len(self.identifiers)} funds, the maximum possible overlap is {len(self.identifiers)}. "
                         "A value of 3 means there's at least one security that appears in 3 different funds."
                )
        
        return overlaps
        
    def get_redundancy_metrics(self):
        """Calculate redundancy metrics"""
        overlaps = self.analyze_overlaps(show_summary=False)  # Don't show summary info here
        metrics = {
            'overlap_count': len([h for h in overlaps.values() if len(h['funds']) > 1]),
            'total_redundant_value': sum(h['total_value'] for h in overlaps.values() if len(h['funds']) > 1),
            'max_overlap': max((len(h['funds']) for h in overlaps.values()), default=1),
        }
        return metrics

def create_overlap_visualization(overlap_data, tickers, fund_types):
    """Create interactive visualization of overlaps with fund type indicators"""
    matrix = pd.DataFrame(0, index=tickers, columns=tickers)
    
    for holding_data in overlap_data.values():
        funds = list(holding_data['funds'])
        for i in range(len(funds)):
            for j in range(i+1, len(funds)):
                matrix.loc[funds[i], funds[j]] += 1
                matrix.loc[funds[j], funds[i]] += 1
    
    # Add fund type indicators to labels
    x_labels = [f"{'📦' if fund_types[t] == 'fund_of_funds' else '📈'} {t}" for t in tickers]
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix.values,
        x=x_labels,
        y=x_labels,
        colorscale=[
            [0, '#f8f9fa'],
            [0.2, '#ffedeb'],
            [0.4, '#ff8c82'],
            [0.6, '#ff6b61'],
            [0.8, '#ff4d40'],
            [1, '#ff3b2e']
        ],
        text=matrix.values,
        texttemplate="%{text}",
        textfont={"size": 12, "color": "white"},
        hoverongaps=False,
    ))
    
    fig.update_layout(
        title="Fund Overlap Matrix (📦 Fund of Funds, 📈 Underlying Fund)",
        xaxis_title="Fund Ticker",
        yaxis_title="Fund Ticker",
        height=600,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'},
    )
    
    return fig

def get_fund_type(session, identifier):
    fund = FundService.get_fund_by_ticker(session, identifier)
    if not fund:
        fund = FundService.get_fund_by_name(session, identifier)
    return fund.fund_type if fund else None

def render_portfolio_analysis(session, identifiers: list[str]):
    """Render portfolio analysis dashboard"""
    if len(identifiers) < 2:
        st.info("Please select at least two funds to analyze portfolio overlaps.")
        return
        
    # Get fund types
    fund_types = {}
    for identifier in identifiers:
        fund = FundService.get_fund_by_ticker(session, identifier)
        if not fund:
            # If not found by ticker, try getting by name
            fund = FundService.get_fund_by_name(session, identifier)
        fund_types[identifier] = fund.fund_type if fund else 'underlying_fund'
    
    # Initialize session state for overlap data if it doesn't exist
    if 'overlap_data' not in st.session_state:
        st.session_state.overlap_data = {}

    # Group funds by type
    fof_funds = [t for t, ft in fund_types.items() if ft == 'fund_of_funds']
    underlying_funds = [t for t, ft in fund_types.items() if ft == 'underlying_fund']
    
    # Initialize analyzer
    analyzer = PortfolioAnalyzer(session, identifiers)
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["Overlap Analysis", "Cost Analysis", "Optimization"])
    
    with tab1:
        # Show fund type groupings
        st.subheader("Selected Funds")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📦 Funds of Funds")
            for fund in fof_funds:
                st.markdown(f"- {fund}")
                
        with col2:
            st.markdown("##### 📈 Underlying Funds")
            for fund in underlying_funds:
                st.markdown(f"- {fund}")
        
        # Overlap Analysis View
        st.subheader("Holdings Overlap Analysis")
        
        # Filter controls
        min_overlap = st.slider("Minimum Overlap Count", 1, len(identifiers), 2)

        # Format the default value with commas
        formatted_default = "{:,}".format(100000)

        # Add a text input for better formatting control
        min_value_str = st.text_input(
            "Minimum Position Value ($)", 
            value=formatted_default,
            key="min_value_input"
        )

        # Convert string with commas to number
        try:
            min_value = float(min_value_str.replace(',', '').replace('$', ''))
        except ValueError:
            st.error("Please enter a valid number")
            min_value = 100000

        # Get overlap data AFTER getting the filter values
        overlaps = analyzer.analyze_overlaps(show_summary=False)  # Don't show summary twice
        
        # Store metrics for use in the chat interface
        metrics = analyzer.get_redundancy_metrics()

        # Filter based on user criteria
        filtered_overlaps = {
            name: data for name, data in overlaps.items()
            if len(data['funds']) >= min_overlap and data['total_value'] >= min_value
        }
        
        # Create visualization with filtered data
        fig = create_overlap_visualization(filtered_overlaps, identifiers, fund_types)
        st.plotly_chart(fig, use_container_width=True)
        
        # Show metrics based on filtered data
        filtered_metrics = {
            'overlap_count': len([h for h in filtered_overlaps.values() if len(h['funds']) > 1]),
            'total_redundant_value': sum(h['total_value'] for h in filtered_overlaps.values() if len(h['funds']) > 1),
            'max_overlap': max((len(h['funds']) for h in filtered_overlaps.values()), default=1),
        }
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Overlapping Holdings", filtered_metrics['overlap_count'])
        col2.metric("Total Redundant Value", f"${filtered_metrics['total_redundant_value']:,.2f}")
        col3.metric("Maximum Overlap", filtered_metrics['max_overlap'])
        
        # Store overlap data in session state for use with the chat interface
        matrix_df = pd.DataFrame(0, index=identifiers, columns=identifiers)
        for holding_data in filtered_overlaps.values():
            funds = list(holding_data['funds'])
            for i in range(len(funds)):
                for j in range(i+1, len(funds)):
                    matrix_df.loc[funds[i], funds[j]] += 1
                    matrix_df.loc[funds[j], funds[i]] += 1
                    
        st.session_state.overlap_data = {
            'selected_funds': identifiers,
            'fund_types': fund_types,
            'metrics': filtered_metrics,
            'detailed_overlaps': filtered_overlaps,
            'matrix': matrix_df,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add a button to ask BiL about this analysis with custom styling
        st.markdown("""
        <style>
        div.stButton > button:first-child {
            background-color: #4285F4;
            color: white;
            font-weight: bold;
        }
        div.stButton > button:hover {
            background-color: #3b77db;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)
        st.button("💬 Ask BiL about this analysis", on_click=lambda: st.session_state.update({'chat_input': '@overlap Please analyze the current fund overlap data and provide insights'}))
        
        # Show detailed overlap table
        st.subheader("Detailed Overlap Analysis")
        if filtered_overlaps:
            overlap_data = []
            for name, data in filtered_overlaps.items():
                overlap_data.append({
                    'Holding': name,
                    'Found In': ', '.join(data['funds']),
                    'Number of Funds': len(data['funds']),
                    'Total Value': f"${data['total_value']:,.2f}"
                })
            
            overlap_df = pd.DataFrame(overlap_data)
            st.dataframe(
                overlap_df.sort_values('Number of Funds', ascending=False),
                use_container_width=True
            )
        else:
            st.info("No overlapping holdings found with current filters")
        
    with tab2:
        # Cost Analysis View
        st.subheader("Cost Impact of Overlaps")
        st.info("Cost analysis feature coming soon!")
        
    with tab3:
        # Optimization Suggestions
        st.subheader("Portfolio Optimization")
        st.info("Optimization suggestions feature coming soon!") 