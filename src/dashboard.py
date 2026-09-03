"""
Streamlit dashboard for the crude oil market intelligence project.
Shows historical WTI/Brent prices, a 30-day forecast, and headline KPIs
in the style of a client-facing energy market deliverable.
"""
import sqlite3

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import DB_PATH

st.set_page_config(page_title="Energy Market Dashboard", layout="wide")


@st.cache_data(ttl=300)
def load_data():
    conn = sqlite3.connect(DB_PATH)
    history = pd.read_sql("SELECT * FROM oil_prices", conn)
    forecast = pd.read_sql("SELECT * FROM oil_price_forecast", conn)
    backtest = pd.read_sql("SELECT * FROM oil_price_backtest", conn)
    conn.close()
    history["date"] = pd.to_datetime(history["date"])
    forecast["date"] = pd.to_datetime(forecast["date"])
    return history, forecast, backtest


st.title("Crude Oil Market Intelligence Dashboard")
st.caption("WTI & Brent price history, 30-day forecast, and market KPIs")

if not DB_PATH.exists():
    with st.spinner("First run: fetching prices and building the forecast..."):
        import fetch_data
        import forecast as forecast_module

        fetch_data.main()
        forecast_module.main()
    st.cache_data.clear()

history, forecast, backtest = load_data()
benchmark = st.selectbox("Benchmark", sorted(history["benchmark"].unique()))

hist_b = history[history["benchmark"] == benchmark].sort_values("date")
fcst_b = forecast[forecast["benchmark"] == benchmark].sort_values("date")
bt_b = backtest[backtest["benchmark"] == benchmark]

latest_price = hist_b["price"].iloc[-1]
price_30d_ago = hist_b["price"].iloc[-30] if len(hist_b) >= 30 else hist_b["price"].iloc[0]
change_30d = (latest_price - price_30d_ago) / price_30d_ago * 100
volatility = hist_b["price"].pct_change().tail(30).std() * 100
forecast_end_price = fcst_b["predicted_price"].iloc[-1] if len(fcst_b) else None

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Latest Price", f"${latest_price:,.2f}")
col2.metric("30-Day Change", f"{change_30d:+.1f}%")
col3.metric("30-Day Volatility", f"{volatility:.2f}%")
if forecast_end_price is not None:
    col4.metric("30-Day Forecast", f"${forecast_end_price:,.2f}")
if len(bt_b):
    col5.metric(
        "Backtested Accuracy",
        f"{bt_b['mape'].iloc[0]:.1f}% MAPE",
        help="Mean Absolute Percentage Error from holding out the last "
        "30 days, refitting on the rest, and comparing the forecast to "
        "what actually happened.",
    )

fig = go.Figure()
fig.add_trace(
    go.Scatter(x=hist_b["date"], y=hist_b["price"], name="Historical", mode="lines")
)
fig.add_trace(
    go.Scatter(
        x=fcst_b["date"],
        y=fcst_b["predicted_price"],
        name="Forecast",
        mode="lines",
        line=dict(dash="dash"),
    )
)
fig.update_layout(
    xaxis_title="Date", yaxis_title="Price (USD/bbl)", legend_title="Series"
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Insight")
direction = "risen" if change_30d > 0 else "fallen"
st.write(
    f"{benchmark} crude has {direction} {abs(change_30d):.1f}% over the last 30 "
    f"trading days, with realized volatility of {volatility:.2f}%. "
    f"The ARIMA model projects prices moving toward "
    f"${forecast_end_price:,.2f}/bbl over the next 30 days."
    if forecast_end_price is not None
    else ""
)
