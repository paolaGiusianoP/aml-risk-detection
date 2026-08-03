import streamlit as st
import pandas as pd
import psycopg2
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Executive Dashboard", page_icon="📈", layout="wide")

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

st.title("Executive Dashboard")
st.markdown("Panel ejecutivo con KPIs globales, tendencias y análisis de riesgos")
st.markdown("---")

try:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM transactions")
    total_trans = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM transactions WHERE \"Is_Laundering\" = 1")
    total_alerts = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM cases")
    total_cases = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM cases WHERE status = 'Cerrado'")
    closed_cases = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM cases WHERE status = 'Escalado'")
    escalated_cases = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(\"Amount_Paid\"), 0) FROM transactions WHERE \"Is_Laundering\" = 1")
    suspicious_amount = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM transactions 
        WHERE \"Is_Laundering\" = 1 
        AND CAST(\"Timestamp\" AS TIMESTAMP) >= NOW() - INTERVAL '24 hours'
    """)
    alerts_24h = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM transactions 
        WHERE \"Is_Laundering\" = 1 
        AND CAST(\"Timestamp\" AS TIMESTAMP) >= NOW() - INTERVAL '7 days'
    """)
    alerts_7d = cursor.fetchone()[0]

    conn.close()

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("💰 Total Transacciones", f"{total_trans:,}")

    with col2:
        st.metric("🚨 Total Alertas", f"{total_alerts:,}", delta=f"{total_alerts/total_trans*100:.4f}%")

    with col3:
        st.metric("📋 Casos Creados", f"{total_cases:,}")

    with col4:
        st.metric("✅ Casos Cerrados", f"{closed_cases:,}", delta=f"{closed_cases/total_cases*100:.1f}%" if total_cases > 0 else "0%")

    with col5:
        st.metric("⚠️ Monto Sospechoso", f"${suspicious_amount:,.2f}")

    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🕐 Alertas últimas 24h", f"{alerts_24h:,}")

    with col2:
        st.metric("📊 Alertas última semana", f"{alerts_7d:,}")

    with col3:
        tasa_resolucion = (closed_cases / total_cases * 100) if total_cases > 0 else 0
        st.metric("📈 Tasa de Resolución", f"{tasa_resolucion:.1f}%")

    with col4:
        st.metric("🔴 Casos Escalados", f"{escalated_cases:,}")

    st.markdown("---")

    st.subheader("📈 Evolución de Alertas (Últimos 30 días)")

    conn = get_connection()
    query_trend = '''
        SELECT 
            DATE(CAST("Timestamp" AS TIMESTAMP)) as date,
            COUNT(*) as alerts
        FROM transactions 
        WHERE "Is_Laundering" = 1 
        AND CAST("Timestamp" AS TIMESTAMP) >= NOW() - INTERVAL '30 days'
        GROUP BY DATE(CAST("Timestamp" AS TIMESTAMP))
        ORDER BY date ASC
    '''
    df_trend = pd.read_sql(query_trend, conn)

    if not df_trend.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_trend['date'],
            y=df_trend['alerts'],
            mode='lines+markers',
            name='Alertas',
            line=dict(color='#ff4444', width=3),
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor='rgba(255,68,68,0.1)'
        ))
        fig.update_layout(
            title="Evolución diaria de alertas",
            xaxis_title="Fecha",
            yaxis_title="Número de alertas",
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos de alertas en los últimos 30 días")

    st.subheader("Heatmap de Actividad Sospechosa")

    query_heatmap = '''
        SELECT 
            EXTRACT(HOUR FROM CAST("Timestamp" AS TIMESTAMP)) as hour,
            EXTRACT(DOW FROM CAST("Timestamp" AS TIMESTAMP)) as day_of_week,
            COUNT(*) as alert_count
        FROM transactions 
        WHERE "Is_Laundering" = 1
        GROUP BY hour, day_of_week
        ORDER BY hour, day_of_week
    '''
    df_heatmap = pd.read_sql(query_heatmap, conn)

    if not df_heatmap.empty:
        pivot = df_heatmap.pivot(index='hour', columns='day_of_week', values='alert_count').fillna(0)
        days = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
        pivot.columns = [days[int(col)] for col in pivot.columns]
        
        fig = px.imshow(
            pivot,
            labels=dict(x="Día de la semana", y="Hora del día", color="Alertas"),
            title="Distribución de alertas por hora y día",
            color_continuous_scale='Reds',
            aspect='auto'
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("🔴 Las áreas más rojas indican mayor concentración de actividad sospechosa")
    else:
        st.info("No hay datos suficientes para el heatmap")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 Cuentas con más Alertas")
        
        query_top_accounts = '''
            SELECT 
                "Account",
                COUNT(*) as alert_count,
                SUM("Amount_Paid") as total_amount
            FROM transactions 
            WHERE "Is_Laundering" = 1
            GROUP BY "Account"
            ORDER BY alert_count DESC
            LIMIT 10
        '''
        df_top_accounts = pd.read_sql(query_top_accounts, conn)
        
        if not df_top_accounts.empty:
            fig = px.bar(
                df_top_accounts,
                x='alert_count',
                y='Account',
                orientation='h',
                title="Cuentas con más alertas",
                labels={'alert_count': 'Número de alertas', 'Account': 'Cuenta'},
                color='alert_count',
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de cuentas con alertas")

    with col2:
        st.subheader("Top 10 Montos Sospechosos")
        
        query_top_amounts = '''
            SELECT 
                "Account",
                "Amount_Paid" as amount,
                "Payment_Format",
                CAST("Timestamp" AS TIMESTAMP) as date
            FROM transactions 
            WHERE "Is_Laundering" = 1
            ORDER BY "Amount_Paid" DESC
            LIMIT 10
        '''
        df_top_amounts = pd.read_sql(query_top_amounts, conn)
        
        if not df_top_amounts.empty:
            fig = px.bar(
                df_top_amounts,
                x='amount',
                y='Account',
                orientation='h',
                title="Mayores montos sospechosos",
                labels={'amount': 'Monto (USD)', 'Account': 'Cuenta'},
                color='amount',
                color_continuous_scale='Reds',
                text='amount'
            )
            fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de montos sospechosos")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Alertas por Formato de Pago")
        
        query_payment = '''
            SELECT 
                "Payment_Format",
                COUNT(*) as alert_count,
                SUM("Amount_Paid") as total_amount
            FROM transactions 
            WHERE "Is_Laundering" = 1
            GROUP BY "Payment_Format"
            ORDER BY alert_count DESC
        '''
        df_payment = pd.read_sql(query_payment, conn)
        
        if not df_payment.empty:
            fig = px.pie(
                df_payment,
                values='alert_count',
                names='Payment_Format',
                title="Distribución de alertas por formato",
                color_discrete_sequence=px.colors.sequential.Reds_r
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de formatos de pago")

    with col2:
        st.subheader("Estado de Casos")
        
        query_status = '''
            SELECT 
                status,
                COUNT(*) as count
            FROM cases
            GROUP BY status
            ORDER BY count DESC
        '''
        df_status = pd.read_sql(query_status, conn)
        
        if not df_status.empty:
            status_colors = {
                'Abierto': '#ffaa00',
                'En revisión': '#3498db',
                'Cerrado': '#00ff9d',
                'Escalado': '#ff4444'
            }
            colors = [status_colors.get(status, '#888888') for status in df_status['status']]
            
            fig = px.pie(
                df_status,
                values='count',
                names='status',
                title="Distribución de casos",
                color_discrete_sequence=colors
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay casos registrados")

    st.markdown("---")

    st.subheader("🚨 Últimas Alertas Generadas")

    query_recent_alerts = '''
        SELECT 
            CAST("Timestamp" AS TIMESTAMP) as Fecha,
            "Account" as Cuenta,
            "Amount_Paid" as Monto,
            "Payment_Format" as Formato,
            CASE 
                WHEN "Amount_Paid" > 50000 THEN 'Alto'
                WHEN "Amount_Paid" > 10000 THEN 'Medio'
                ELSE 'Bajo'
            END as Severidad
        FROM transactions 
        WHERE "Is_Laundering" = 1 
        ORDER BY CAST("Timestamp" AS TIMESTAMP) DESC 
        LIMIT 20
    '''
    df_recent = pd.read_sql(query_recent_alerts, conn)
    conn.close()

    if not df_recent.empty:
        st.dataframe(
            df_recent,
            use_container_width=True,
            column_config={
                "Monto": st.column_config.NumberColumn("Monto", format="$%.2f"),
                "Severidad": st.column_config.TextColumn("Severidad"),
            }
        )
        
        csv = df_recent.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exportar a CSV",
            data=csv,
            file_name=f"alertas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No hay alertas recientes")

    st.markdown("---")
    st.caption(f"📅 Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption("🛡️ AML Risk Detection Platform | Financial Crime Analytics")

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