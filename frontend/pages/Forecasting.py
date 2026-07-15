import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.api_client import fetch_json

st.set_page_config(page_title="Forecasting", page_icon="🔮", layout="wide")

st.title("Forecasting")

try:
    monthly_sales = fetch_json("/sales/monthly")
except Exception as exc:
    st.error(f"Unable to load historical sales: {exc}")
    st.stop()

try:
    forecast = fetch_json("/forecast")
except Exception as exc:
    st.error(f"Unable to load forecast: {exc}")
    st.stop()

history_df = pd.DataFrame(monthly_sales)
forecast_df = pd.DataFrame(forecast.get("series", []))

col1, col2 = st.columns(2)
with col1:
    st.metric("Forecast Horizon", f"{forecast.get('forecast_horizon_months', 0)} months")
with col2:
    st.metric("Confidence Interval", f"{forecast.get('confidence_interval', 0) * 100:.0f}%")

fig = go.Figure()
if not history_df.empty:
    fig.add_trace(
        go.Scatter(
            x=history_df["month"],
            y=history_df["revenue"],
            mode="lines",
            name="Historical Revenue",
            line=dict(color="#1f77b4"),
        )
    )
if not forecast_df.empty:
    if "upper_bound" in forecast_df and "lower_bound" in forecast_df:
        fig.add_trace(
            go.Scatter(
                x=pd.concat([forecast_df["month"], forecast_df["month"][::-1]]),
                y=pd.concat([forecast_df["upper_bound"], forecast_df["lower_bound"][::-1]]),
                fill="toself",
                fillcolor="rgba(255,127,14,0.15)",
                line=dict(color="rgba(255,255,255,0)"),
                name="Confidence Interval",
                showlegend=True,
            )
        )
    fig.add_trace(
        go.Scatter(
            x=forecast_df["month"],
            y=forecast_df["forecast"],
            mode="lines+markers",
            name="Forecast",
            line=dict(color="#ff7f0e", dash="dash"),
        )
    )

fig.update_layout(
    xaxis_title="Month",
    yaxis_title="Revenue ($)",
    hovermode="x unified",
)
st.plotly_chart(fig, use_container_width=True)

st.caption(forecast.get("note", ""))

st.subheader("Forecast Detail")
st.dataframe(forecast_df, use_container_width=True)

