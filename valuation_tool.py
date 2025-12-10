import streamlit as st
import yfinance as yf
import pandas as pd # Import pandas for dataframes/tables

st.set_page_config(page_title="Stock Valuator", layout="centered")

st.header("📱 Stock Valuation Tool")

# --- Inputs (Collapsible for Mobile) ---
with st.expander("1. Stock & Assumptions (Tap to Open)", expanded=True):
    ticker_symbol = st.text_input("Ticker Symbol", value="AAPL").upper()

    st.markdown("---")
    st.write("**Growth Assumptions**")
    revenue_growth = st.number_input("Growth Rate (%)", value=10.0, step=0.5) / 100
    required_return = st.number_input("Required Return (%)", value=10.0, step=0.5) / 100
    years = st.slider("Years to Project", 1, 10, 5)

    st.write("**Valuation Multiples**")
    target_pe = st.number_input("Target P/E", value=20.0)
    target_pfcf = st.number_input("Target P/FCF", value=20.0)

# --- Logic & Display ---
if ticker_symbol:
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info

        current_price = info.get('currentPrice', 0.0)
        ttm_eps = info.get('trailingEps', 0.0)

        try:
            # FCF Calculation (FCF / Shares Outstanding)
            fcf_per_share = info.get('freeCashflow', 0) / info.get('sharesOutstanding', 1)
        except:
            fcf_per_share = 0.0

        if current_price == 0:
            st.warning("Could not fetch live price. Check Ticker.")
            st.stop()

        # 1. Project Future Metrics
        future_eps = ttm_eps * ((1 + revenue_growth) ** years)
        future_fcf = fcf_per_share * ((1 + revenue_growth) ** years)

        # 2. Future Price
        future_price_pe = future_eps * target_pe
        future_price_fcf = future_fcf * target_pfcf

        # 3. Intrinsic Value (Discounted)
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
            "Method": ["Based on Earnings (P/E)", "Based on Cash Flow (P/FCF)"],
            "Fair Value": [f"${intrinsic_pe:.2f}", f"${intrinsic_fcf:.2f}"]
        })
        st.dataframe(df, hide_index=True, use_container_width=True)

    except Exception as e:
        st.error(f"Error fetching or calculating data. Check the ticker or input values. Details: {e}")

