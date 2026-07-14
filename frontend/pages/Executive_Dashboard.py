import streamlit as st

from utils.api_client import fetch_json

st.set_page_config(page_title="Executive Dashboard", page_icon="📈", layout="wide")

st.title("Executive Dashboard")

try:
    summary = fetch_json("/sales/summary")
except Exception as exc:
    st.error(f"Unable to load sales summary: {exc}")
    st.stop()

summary = summary or {}
st.write(summary)

revenue = summary.get("total_revenue", 0)
orders = summary.get("total_orders", 0)
avg_order_value = summary.get("average_order_value", 0)
top_region = summary.get("top_region", "N/A")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Revenue", f"${float(revenue):,}")
with col2:
    st.metric("Orders", f"{int(orders):,}")
with col3:
    st.metric("Avg Order Value", f"${float(avg_order_value):.2f}")
with col4:
    st.metric("Top Region", top_region)

st.caption("TODO: Replace mock metrics with warehouse-backed KPIs and richer executive storytelling.")
