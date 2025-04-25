import streamlit as st
import plotly.graph_objects as go
from src.services.fund_service import FundService
import pandas as pd

def prepare_holdings_data(holdings_df: pd.DataFrame) -> pd.DataFrame:
    """Add Value_Numeric column and other necessary transformations."""
    if holdings_df.empty:
        return holdings_df
    df = holdings_df.copy()
    df['Value_Numeric'] = df['Value'].str.replace('$', '').str.replace(',', '').astype(float)
    return df

def render_fund_structure(session, ticker: str):
    """Render a hierarchical view of fund holdings with top 10 underlying holdings."""
    holdings = FundService.get_holdings_details(session, ticker)
    holdings = prepare_holdings_data(holdings)
    
    # First level table
    st.subheader("Level 1: Direct Fund Holdings")
    # Sort by Value_Numeric first, then select display columns
    sorted_holdings = holdings.sort_values('Value_Numeric', ascending=False)
    st.dataframe(
        sorted_holdings[['Name', 'Value', 'Pct', 'Category']]
    )
    
    # Second level table
    st.subheader("Level 2: Top Holdings of Each Underlying Fund")
    for _, holding in holdings.iterrows():
        if holding['Ticker'] and holding['Ticker'] != 'None':
            with st.expander(f"{holding['Name']} ({holding['Pct']}%)"):
                underlying = FundService.get_holdings_details(session, holding['Ticker'])
                if not underlying.empty:
                    underlying = prepare_holdings_data(underlying)
                    # Sort first, then select display columns
                    sorted_underlying = underlying.nlargest(10, 'Value_Numeric')
                    st.dataframe(
                        sorted_underlying[['Name', 'Value', 'Pct', 'Category']]
                    )
    
    # Sankey diagram with top 10 holdings for each fund
    nodes = []
    links = []
    node_map = {ticker: 0}  # Map fund names to node indices
    
    # Add parent fund node
    nodes.append({
        'name': ticker,
        'type': 'FOF',
        'value': holdings['Value_Numeric'].sum()
    })
    
    # Process each underlying fund
    for _, holding in holdings.iterrows():
        # Add holding node
        holding_name = holding['Name']
        if holding_name not in node_map:
            node_map[holding_name] = len(nodes)
            nodes.append({
                'name': holding_name,
                'type': 'Mutual Fund',
                'value': float(str(holding['Value']).replace('$', '').replace(',', ''))
            })
        
        # Add link from parent to holding
        links.append({
            'source': node_map[ticker],
            'target': node_map[holding_name],
            'value': float(str(holding['Value']).replace('$', '').replace(',', '')),
            'percentage': holding['Pct']
        })
        
        # Get top 10 underlying holdings
        if holding['Ticker'] and holding['Ticker'] != 'None':
            underlying = FundService.get_holdings_details(session, holding['Ticker'])
            if not underlying.empty:
                # Prepare data first
                underlying = prepare_holdings_data(underlying)
                top_10 = underlying.nlargest(10, 'Value_Numeric')
                
                for _, stock in top_10.iterrows():
                    stock_name = stock['Name']
                    if stock_name not in node_map:
                        node_map[stock_name] = len(nodes)
                        nodes.append({
                            'name': stock_name,
                            'type': 'Stock',
                            'value': stock['Value_Numeric']  # Use prepared numeric value
                        })
                    
                    # Add link from fund to stock
                    links.append({
                        'source': node_map[holding_name],
                        'target': node_map[stock_name],
                        'value': float(str(stock['Value']).replace('$', '').replace(',', '')),
                        'percentage': stock['Pct']
                    })
    
    # Create Sankey diagram with hover events
    fig = go.Figure(data=[go.Sankey(
        node = dict(
            pad = 15,
            thickness = 20,
            line = dict(color = "black", width = 0.5),
            label = [node['name'] for node in nodes],
            color = [get_fund_color(node['type']) for node in nodes],
            customdata = list(range(len(nodes))),
            hoverinfo = 'all',
        ),
        link = dict(
            source = [link['source'] for link in links],
            target = [link['target'] for link in links],
            value = [link['value'] for link in links],
            color = ['rgba(200, 200, 200, 0.5)'] * len(links),
            customdata = [link['percentage'] for link in links],
            hovertemplate = 'From %{source.label}<br>' +
                           'To %{target.label}<br>' +
                           'Value: $%{value:,.2f}<br>' +
                           'Percentage: %{customdata:.1f}%<extra></extra>'
        )
    )])
    
    # Store node colors for reference
    node_colors = [get_fund_color(node['type']) for node in nodes]

    # Update layout with better title positioning
    fig.update_layout(
        title=dict(
            text=f"Fund Structure: {ticker}",
            y=0.95,  # Move title up
            x=0.5,
            xanchor='center',
            yanchor='top',
            font=dict(size=16)
        ),
        font_size=10,
        height=800,
        margin=dict(t=60, l=0, r=0, b=0),  # Increase top margin
        hovermode='closest',
        paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
    )

    # Add hover and drag instructions
    fig.add_annotation(
        dict(
            text='Hover over nodes to highlight flows • Drag nodes to rearrange',
            xref='paper',
            yref='paper',
            x=0,
            y=1.02,  # Move instruction text up
            showarrow=False,
            font=dict(size=12)
        )
    )

    # Create container for the chart
    chart_container = st.empty()
    
    # Config with event handling
    config = {
        'displayModeBar': True,
        'modeBarButtonsToRemove': ['lasso', 'select'],
        'displaylogo': False,
        'responsive': True,
    }

    # Display the chart with event handling
    chart = chart_container.plotly_chart(
        fig, 
        use_container_width=True, 
        config=config,
        custom_events=['plotly_hover', 'plotly_unhover']  # Enable hover events
    )

    # Get hover event data
    hover_data = st.session_state.get('plotly_hover')
    if hover_data and 'points' in hover_data and hover_data['points']:
        point = hover_data['points'][0]
        if 'pointNumber' in point and point['curveNumber'] == 0:  # Check if hovering on node
            node_index = point['pointNumber']
            node_color = node_colors[node_index]
            
            # Update link colors
            new_colors = []
            for i, (_, target) in enumerate(zip(fig.data[0].link.source, fig.data[0].link.target)):
                if target == node_index:
                    new_colors.append(node_color)
                else:
                    new_colors.append('rgba(200, 200, 200, 0.5)')
            
            # Update the figure
            fig.update_traces(link_color=new_colors)
            chart_container.plotly_chart(fig, use_container_width=True, config=config)

def get_fund_color(fund_type: str) -> str:
    """Get color based on fund type."""
    colors = {
        'FOF': '#1f77b4',  # Blue for Fund of Funds
        'Mutual Fund': '#2ca02c',  # Green for regular mutual funds
        'Stock': '#ff7f0e',  # Orange for stocks
        'Other': '#7f7f7f'  # Gray for others
    }
    return colors.get(fund_type, colors['Other']) 