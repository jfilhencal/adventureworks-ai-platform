import streamlit as st

from utils.api_client import post_json

st.title("AI Assistant")

prompt = st.text_area("Ask the platform about revenue, product trends, or potential anomalies")
if st.button("Analyze") and prompt:
    response = post_json("/ai/analyze", {"prompt": prompt})
    st.write(response.get("summary", "Our business analyst must be taking a nap... Please try again later."))

