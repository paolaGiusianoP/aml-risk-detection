import streamlit as st
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="AML Risk Detection Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_connection():
    """Obtiene conexión a la base de datos"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    if not DATABASE_URL:
        try:
            DATABASE_URL = st.secrets.get("DATABASE_URL")
        except:
            pass
    
    if not DATABASE_URL:
        return None
    
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None


st.title("🛡️ AML Risk Detection Platform")
st.markdown("*Financial Crime Analytics • Machine Learning • Real-time Monitoring*")
st.markdown("---")

DEBUG_MODE = os.getenv('DEBUG', 'false').lower() == 'true'

if DEBUG_MODE:
    st.subheader("Diagnóstico de Conexión")
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        try:
            DATABASE_URL = st.secrets.get("DATABASE_URL")
        except:
            pass

    col1, col2 = st.columns(2)

    with col1:
        st.metric("DATABASE_URL configurada", "Sí" if DATABASE_URL else "No")

    if DATABASE_URL:
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM transactions')
                count = cursor.fetchone()[0]
                st.success(f"Conexión exitosa. Transacciones: {count:,}")
                
                cursor.execute('SELECT COUNT(*) FROM transactions WHERE "Is_Laundering" = 1')
                suspicious = cursor.fetchone()[0]
                st.info(f"🚨 Transacciones sospechosas: {suspicious:,}")
                
                conn.close()
            except Exception as e:
                st.error(f"Error en consulta: {e}")
        else:
            st.error("No se pudo conectar a la base de datos")
    else:
        st.error("DATABASE_URL NO configurada")
    
    st.markdown("---")


st.subheader("Módulos")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.page_link("pages/1_Transaction_Monitoring.py", label="🏦 Transaction Monitoring")
with col2:
    st.page_link("pages/2_Risk_Scoring.py", label="📊 Risk Scoring")
with col3:
    st.page_link("pages/3_Anomaly_Detection.py", label="⚠️ Anomaly Detection")
with col4:
    st.page_link("pages/4_Case_Management.py", label="📋 Case Management")
with col5:
    st.page_link("pages/5_Executive_Dashboard.py", label="📈 Executive Dashboard")


st.markdown("---")
st.caption("🛡️ AML Risk Detection Platform | Powered by Streamlit")