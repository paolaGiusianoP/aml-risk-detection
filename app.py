import streamlit as st

st.set_page_config(
    page_title="AML Risk Detection Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Header principal
st.markdown("""
# AML Risk Detection Platform

*Financial Crime Analytics • Machine Learning • Real-time Monitoring*

Sistema de detección de actividades sospechosas para prevención de lavado de activos (AML).
""")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.page_link("pages/Transaction_Monitoring.py", label="🏦 Transaction Monitoring")
with col2:
    st.page_link("pages/Risk_Scoring.py", label="📊 Risk Scoring")
with col3:
    st.page_link("pages/Anomaly_Detection.py", label="⚠️ Anomaly Detection")
with col4:
    st.page_link("pages/Case_Management.py", label="📋 Case Management")
with col5:
    st.page_link("pages/Executive_Dashboard.py", label="📈 Executive Dashboard")

# Stack tecnológico
st.markdown("---")
st.markdown("### 🛠 Stack Tecnológico")

tech_cols = st.columns(4)
with tech_cols[0]:
    st.markdown("**Data Engineering**\n- Python\n- Pandas/NumPy\n- PostgreSQL")
with tech_cols[1]:
    st.markdown("**Machine Learning**\n- Scikit-learn\n- XGBoost\n- Random Forest")
with tech_cols[2]:
    st.markdown("**Visualization**\n- Streamlit\n- Plotly\n- Altair")
with tech_cols[3]:
    st.markdown("**Tools**\n- Git/GitHub\n- SQL\n- Docker")