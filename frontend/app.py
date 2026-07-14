import streamlit as st

from utils.api_client import fetch_json

st.set_page_config(page_title="AdventureWorks AI Platform", page_icon="📊", layout="wide")

st.title("AdventureWorks AI Analytics Platform")
st.caption("A production-style portfolio project spanning warehousing, analytics, forecasting, and generative AI.")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Service Status", "Online")
with col2:
    st.metric("Data Sources", "SQL + Azure")
with col3:
    st.metric("AI Layer", "Foundry Ready")

if st.button("Refresh API Health"):
    health = fetch_json("/health")
    st.json(health)

st.markdown("### Navigation")
st.info("Use the sidebar to explore the executive dashboard, sales analysis, forecasting, and AI assistant experiences.")
