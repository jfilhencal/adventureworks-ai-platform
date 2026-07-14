import pandas as pd
import plotly.express as px
import streamlit as st

from utils.api_client import fetch_json

st.title("Sales Analysis")
monthly = fetch_json("/sales/monthly")
df = pd.DataFrame(monthly)

fig = px.line(df, x="month", y="revenue", title="Monthly Revenue Trend")
st.plotly_chart(fig, use_container_width=True)

st.dataframe(df, use_container_width=True)
