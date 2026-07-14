import streamlit as st

from utils.api_client import fetch_json

st.title("Forecasting")
forecast = fetch_json("/forecast")
st.json(forecast)
st.caption("TODO: Integrate Prophet-based forecasting with historical AdventureWorksDW series.")
