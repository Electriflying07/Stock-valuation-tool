import streamlit as st
import yfinance as yf
import pandas as pd

# --- Mobile Config ---
st.set_page_config(page_title="Stock Valuator (Margin Model)", layout="centered")

st.header("📱 Stock Valuation Tool (Margin Model)")

# --- Inputs (Collapsible for Mobile) ---
with st.expander("1. Stock & Assumptions (Tap to Open)", expanded=True):
    ticker_symbol = st.text_input("Ticker Symbol", value="PYPL").upper()
    
    st.markdown("---")
    st.write("**Financial Inputs**")
    
    # NEW INPUT: Base Revenue and Margin Targets
    current_revenue = st.number_input("Current Annual Revenue (in Billions)", min_value=0.1, value=29.7, step=0.1)
    
    st.write("**Growth & Margins**")
    revenue_growth = st.number_input("Projected Annual Revenue Growth (%)", value=6.0, step=0.5) / 100
    target_profit_margin = st.number_input("Target Net Profit Margin (%)", min_value=0.0, value=15.0, step=0.5) / 100
    target_fcf_margin = st.number_input("Target FCF Margin (%)", min_value=0.0, value=18.0, step=0.5) / 100
    
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
        
        # Live Data
        current_price = info.get('currentPrice', 0.0)
        shares_out = info.get('sharesOutstanding', 1)
        
        if current_price == 0 or shares_out == 1:
            st.warning("Could not fetch essential live data. Check Ticker.")
            st.stop()

        # --- Calculations ---
        
        # 1. Project Future Revenue
        future_revenue = current_revenue * (10**9) * ((1 + revenue_growth) ** years)
        
        # 2. Project Future Earnings (Net Income) and FCF
        future_net_income = future_revenue * target_profit_margin
        future_fcf_total = future_revenue * target_fcf_margin
        
        # 3. Calculate Future EPS and FCF per Share
        future_eps = future_net_income / shares_out
        future_fcf_per_share = future_fcf_total / shares_out
        
        # 4. Future Price
        future_price_pe = future_eps * target_pe
        future_price_fcf = future_fcf_per_share * target_pfcf
        
        # 5. Intrinsic Value (Discounted)
        intrinsic_pe = future_price_pe / ((1 + required_return) ** years)
        intrinsic_fcf = future_price_fcf / ((1 + required_return) ** years)
        
        avg_value = (intrinsic_pe + intrinsic_fcf) / 2
        
        # Status
        diff = (avg_value - current_price) / current_price * 100
        is_buy = avg_value > current_price

        # --- Mobile Dashboard ---
        st.markdown("---")
        st.subheader(f"Results: {ticker_symbol}")
        
        col1, col2 = st.columns(2)
        col1.metric("Live Price", f"${current_price:.2f}")
        col2.metric("Fair Value", f"${avg_value:.2f}", 
                    delta=f"{diff:.1f}%", 
                    delta_color="normal")

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


    except Exception as e:
        st.error(f"Error fetching or calculating data. Check the ticker or input values. Details: {e}")
        
