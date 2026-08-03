import streamlit as st

import pandas as pd

import psycopg2

import plotly.express as px

import plotly.graph_objects as go

from datetime import datetime

import os



st.set_page_config(page_title="Transaction Monitoring", page_icon="🏦", layout="wide")



def get_connection():
    try:
        DATABASE_URL = st.secrets.get("DATABASE_URL")
        if DATABASE_URL:
            return psycopg2.connect(DATABASE_URL)
    except:
        pass
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        raise Exception("DATABASE_URL no configurada")
    
    return psycopg2.connect(DATABASE_URL)


st.title("Transaction Monitoring")

st.markdown("Monitoreo de transacciones y detección de actividades sospechosas")

st.markdown("---")



try:

    conn = get_connection()

    cursor = conn.cursor()



    cursor.execute('SELECT COUNT(*) FROM transactions')

    total_trans = cursor.fetchone()[0]



    cursor.execute('SELECT COUNT(*) FROM transactions WHERE "Is_Laundering" = 1')

    suspicious_trans = cursor.fetchone()[0]



    cursor.execute('SELECT COALESCE(SUM("Amount_Paid"), 0) FROM transactions')

    total_amount = cursor.fetchone()[0]



    cursor.execute('SELECT COALESCE(SUM("Amount_Paid"), 0) FROM transactions WHERE "Is_Laundering" = 1')

    suspicious_amount = cursor.fetchone()[0]



    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric("📊 Total Transacciones", f"{total_trans:,}")

    with col2:

        st.metric("🚨 Alertas Generadas", f"{suspicious_trans:,}", delta=f"{suspicious_trans/total_trans*100:.4f}%")

    with col3:

        st.metric("💰 Monto Total", f"${total_amount:,.2f}")

    with col4:

        st.metric("⚠️ Monto Sospechoso", f"${suspicious_amount:,.2f}")



    st.markdown("---")



    query = '''

        SELECT DATE("Timestamp") as date, COUNT(*) as total,

        SUM(CASE WHEN "Is_Laundering" = 1 THEN 1 ELSE 0 END) as suspicious

        FROM transactions GROUP BY DATE("Timestamp") ORDER BY date DESC LIMIT 30

    '''

    df_trend = pd.read_sql(query, conn)

    df_trend = df_trend.sort_values('date')



    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df_trend['date'], y=df_trend['total'], mode='lines+markers', name='Total', line=dict(color='#00ff9d')))

    fig.add_trace(go.Scatter(x=df_trend['date'], y=df_trend['suspicious'], mode='lines+markers', name='Sospechosas', line=dict(color='#ff4444')))

    fig.update_layout(title="Evolución diaria", height=400)

    st.plotly_chart(fig, use_container_width=True)



    st.subheader("🚨 Últimas Alertas")

    query_alerts = '''

        SELECT "Timestamp", "Account", "Amount_Paid", "Payment_Format"

        FROM transactions WHERE "Is_Laundering" = 1 ORDER BY "Timestamp" DESC LIMIT 50

    '''

    df_alerts = pd.read_sql(query_alerts, conn)

    st.dataframe(df_alerts, use_container_width=True)



    conn.close()



except Exception as e:

    st.error(f"Error de conexión a la base de datos: {e}")

    st.info("Verifica que DATABASE_URL esté configurada en Render y que los datos estén cargados en Neon.tech")

    

    try:

        df_demo = pd.read_csv('data/processed/transactions_sample.csv')

        st.subheader("Datos de demostración")

        st.dataframe(df_demo.head(100), use_container_width=True)

        st.caption("Mostrando datos de muestra desde CSV")

    except FileNotFoundError:

        st.warning("No se encontraron datos de demostración")



st.caption(f"📅 Actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")