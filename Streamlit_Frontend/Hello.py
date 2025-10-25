import streamlit as st

st.set_page_config(
    page_title="Smart Nutrition Planner",
    page_icon="👋",
)

st.write("# Welcome to Smart Nutrition Planner! 👋")

st.sidebar.success("Select a recommendation app.")

st.markdown(
    """
    A Smart Nutrition Planner application using content-based approach with Scikit-Learn, FastAPI and Streamlit.
    """
)
