import streamlit as st
import pandas as pd

def display_fund_detail(fund_info: dict):
    """Display detailed fund information"""
    if not fund_info:
        return
    
    st.subheader("Fund Details")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Fund Name", fund_info.get('name', 'N/A'))
        st.metric("CIK", fund_info.get('cik', 'N/A'))
    
    with col2:
        st.metric("Fund Type", fund_info.get('fund_type', 'N/A'))
        st.metric("CUSIP", fund_info.get('cusip', 'N/A'))
    
    if 'holdings' in fund_info:
        st.subheader("Holdings")
        holdings_df = pd.DataFrame(fund_info['holdings'])
        st.dataframe(holdings_df) 