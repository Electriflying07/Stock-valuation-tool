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
        recent_margins = data.iloc[-years:]
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
    
    # --- Start Main Execution Block ---
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
        if len(revenue_data) > 0 and len(net_income_data) > 0:
            # Create a series of historical profit margins (Net Income / Revenue)
            historical_margins = (net_income_data / revenue_data).dropna()
        else:
            historical_margins = pd.Series([0.0])

        # Historical Average Margins
        avg_margin_1y = historical_margins.iloc[-1] if not historical_margins.empty else 0.0
        avg_margin_5y = calculate_avg_margin(historical_margins, 5)
        avg_margin_10y = calculate_avg_margin(historical_margins, 10)

        # --- Display Historical Data ---
        st.markdown("---")
        st.subheader("2. Historical Financial Context")
        
        # Revenue Input
        current_revenue_B = current_revenue / 1e9
        current_revenue_B_input = st.number_input(
            "Current Annual Revenue (in Billions)",
            min_value=0.1, 
            value=float(f"{current_revenue_B:.2f}"), 
            step=0.1
        )
        current_revenue_for_calc = current_revenue_B_input * 1e9
        
        col_r, col_m = st.columns(2)
        
        with col_r:
            st.caption("Revenue Growth (CAGR)")
            historical_data_r = {
                "Period": ["Last Year (TTM)", "Last 5 Years", "Last 10 Years"],
                "Growth Rate": [f"{cagr_1y * 100:.2f}%", f"{cagr_5y * 100:.2f}%", f"{cagr_10y * 100:.2f}%"]
            }
            st.dataframe(pd.DataFrame(historical_data_r), hide_index=True, use_container_width=True)
            
        with col_m:
            st.caption("Net Profit Margin (Average)")
            historical_data_m = {
                "Period": ["Last Year (TTM)", "Last 5 Years", "Last 10 Years"],
                "Margin": [f"{avg_margin_1y * 100:.2f}%", f"{avg_margin_5y * 100:.2f}%", f"{avg_margin_10y * 100:.2f}%"]
            }
            st.dataframe(pd.DataFrame(historical_data_m), hide_index=True, use_container_width=True)

        st.markdown("---")
        st.subheader("3. Future Growth and Margins Assumptions")
        
        # Margin and Projection Inputs
        revenue_growth = st.number_input("Projected Annual Revenue Growth (%)", value=6.0, step=0.5) / 100
        target_profit_margin = st.number_input("Target Net Profit Margin (%)", min_value=0.0, value=15.0, step=0.5) / 100
        target_fcf_margin = st.number_input("Target FCF Margin (%)", min_value=0.0, value=18.0, step=0.5) / 100

        # --- VALUATION CALCULATIONS ---
        
        # 1. Project Future Revenue
        future_revenue = current_revenue_for_calc * np.power((1 + revenue_growth), years)
        
        # 2. Project Future Earnings (Net Income) and FCF
        future_net_income = future_revenue * target_profit_margin 
        future_fcf_total = future_revenue * target_fcf_margin
        
        # 3. Calculate Future Per Share Metrics
        future_eps = future_net_income / shares_out
        future_fcf_per_share = future_fcf_total / shares_out
        
        # 4. Future Price
        future_price_pe = future_eps * target_pe
        future_price_fcf = future_fcf_per_share * target_pfcf
        
        # 5. Intrinsic Value (Discounted)
        intrinsic_pe = future_price_pe / np.power((1 + required_return), years)
        intrinsic_fcf = future_price_fcf / np.power((1 + required_return), years)
        
        avg_value = (intrinsic_pe + intrinsic_fcf) / 2
        
        # Status
        diff = (avg_value - current_price) / current_price * 100
        is_buy = avg_value > current_price

        # --- RESULTS DISPLAY ---
        st.markdown("---")
        st.subheader(f"4. Valuation Results: {ticker_symbol}")
        
        col1, col2 = st.columns(2)
        col1.metric("Live Price", f"${current_price:.2f}")
        col2.metric("Fair Value", f"${avg_value:.2f}", 
                    delta=f"{diff:.1f}%", 
                    delta_color="normal")
        
        # FIX: The entire f-string below is now on a single, continuous line to prevent newline errors.
        if is_buy:
            st.success(f"✅ **UNDERVALUED** by {abs(diff):.1f}% based on your assumptions.")
        else:
            st.error(f"❌ **OVERVALUED** by {abs(diff):.1f}% based on your assumptions.")

        st.caption("Valuation Breakdown")
        df = pd.DataFrame({
            "Metric": ["Future Revenue", "Future EPS", "Future FCF/Share"],
            f"Value in {years} Yrs": [f"${future_revenue/10**9:.1f}B", f"${future_eps:.2f}", f"${future_fcf_per_share:.2f}"] 
        })
        st.dataframe(df, hide_index=True, use_container_width=True) 

        st.caption("Intrinsic Value Comparison")
        df2 = pd.DataFrame({
            "Method": ["Based on Earnings (P/E)", "Based on Cash Flow (P/FCF)"],
            "Fair Value": [f"${intrinsic_pe:.2f}", f"${intrinsic_fcf:.2f}"]
        })
        st.dataframe(df2, hide_index=True, use_container_width=True)


    # --- End Main Execution Block with Exception Handler ---
    except Exception as e:
        st.error(f"A critical error occurred during data processing. Please ensure your Ticker is correct and refresh the page. Error details: {e}")
        
