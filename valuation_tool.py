import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np 

# --- Helper Function for CAGR Calculation ---
def calculate_cagr(start_value, end_value, years):
    """Calculates Compound Annual Growth Rate (CAGR)."""
    if start_value > 0 and end_value > 0 and years > 0 and years < 100:
        try:
            cagr = np.power((end_value / start_value), (1 / years)) - 1
            return cagr
        except Exception:
            return 0.0
    return 0.0

# --- Helper Function for Average Margin Calculation ---
def calculate_avg_margin(data, years):
    """Calculates the average profit margin over the specified number of years."""
    if len(data) >= years:
        # Get the last 'years' worth of margins
        recent_margins = data.iloc[-years:]
        # Calculate the simple average of those margins
        return recent_margins.mean()
    return 0.0

# --- Mobile Config ---
st.set_page_config(page_title="Stock Valuator (Historical Margins)", layout="centered")

st.header("📈 Stock Valuation Tool (Historical Margins)")

# --- Inputs (Collapsible for Mobile) ---
with st.expander("1. Stock & Assumptions (Tap to Open)", expanded=True):
    ticker_symbol = st.text_input("Ticker Symbol", value="PYPL").upper()
    
    st.write("**Discount & Multiples**")
    required_return = st.number_input("Required Return (%)", value=12.0, step=0.5) / 100
    years = st.slider("Years to Project", 1, 10, 10)
    target_pe = st.number_input("Target P/E Multiplier (Year End)", value=15.0)
    target_pfcf = st.number_input("Target P/FCF Multiplier (Year End)", value=18.0)

# --- Logic & Display ---
if ticker_symbol:
    
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        
        current_price = info.get('currentPrice', 0.0)
        shares_out = info.get('sharesOutstanding', 1)
        
        if current_price == 0 or shares_out == 1:
            st.warning("Could not fetch essential live data (Price or Shares Outstanding). Check Ticker.")
            st.stop()
            
        # --- SAFELY FETCH FINANCIAL DATA ---
        financials = stock.financials.T.sort_index(ascending=True) 
        
        # 1. Revenue Data
        revenue_data = financials.get('Total Revenue', pd.Series()).dropna()
        current_revenue = revenue_data.iloc[-1] if not revenue_data.empty else info.get('totalRevenue', 0)
        if current_revenue == 0:
            st.warning("Could not fetch current annual revenue.")
        
        # 2. Net Income Data
        net_income_data = financials.get('Net Income', pd.Series()).dropna()
        
        # --- CALCULATE HISTORICAL GROWTH & MARGINS ---
        
        # Revenue CAGRs
        cagr_1y = calculate_cagr(revenue_data.iloc[-2], current_revenue, 1) if len(revenue_data) >= 2 else 0.0
        cagr_5y = calculate_cagr(revenue_data.iloc[-5], current_revenue, 5) if len(revenue_data) >= 5 else 0.0
        cagr_10y = calculate_cagr(revenue_data.iloc[-10], current_revenue, 10) if len(revenue_data) >= 10 else 0.0
        
        # Profit Margins
        
