import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="Risk Scoring", page_icon="📊", layout="wide")

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

st.title("Risk Scoring")
st.markdown("Cálculo de nivel de riesgo por cliente basado en comportamiento transaccional")
st.markdown("---")

def calculate_risk_score(row):
    score = 0
    
    suspicious_ratio = row['suspicious_ratio']
    if suspicious_ratio > 0.1:
        score += 40
    elif suspicious_ratio > 0.05:
        score += 30
    elif suspicious_ratio > 0.01:
        score += 20
    elif suspicious_ratio > 0:
        score += 10
    
    avg_amount = row['avg_amount']
    if avg_amount > 50000:
        score += 25
    elif avg_amount > 20000:
        score += 18
    elif avg_amount > 10000:
        score += 12
    elif avg_amount > 5000:
        score += 6
    
    txn_count = row['total_trans']
    if txn_count > 1000:
        score += 20
    elif txn_count > 500:
        score += 14
    elif txn_count > 100:
        score += 8
    elif txn_count > 50:
        score += 4
    
    risk_formats = row.get('risk_payment_formats', 0)
    score += min(risk_formats * 5, 15)
    
    return min(score, 100)

def get_risk_level(score):
    if score >= 70:
        return "Alto Riesgo", "🔴", "#ff4444"
    elif score >= 40:
        return "Riesgo Medio", "🟡", "#ffaa00"
    else:
        return "Bajo Riesgo", "🟢", "#00ff9d"

try:
    conn = get_connection()
    
    query = '''
        SELECT 
            "Account",
            COUNT(*) as total_trans,
            SUM(CASE WHEN "Is_Laundering" = 1 THEN 1 ELSE 0 END) as suspicious_trans,
            SUM("Amount_Paid") as total_amount,
            AVG("Amount_Paid") as avg_amount,
            MAX("Amount_Paid") as max_amount,
            MIN("Amount_Paid") as min_amount,
            STDDEV("Amount_Paid") as stddev_amount,
            COUNT(DISTINCT "Payment_Format") as unique_payment_formats,
            STRING_AGG(DISTINCT "Payment_Format", ', ') as payment_formats,
            MIN("Timestamp") as first_txn,
            MAX("Timestamp") as last_txn
        FROM transactions
        GROUP BY "Account"
        ORDER BY suspicious_trans DESC
    '''
    
    with st.spinner("Calculando scores de riesgo..."):
        df_risk = pd.read_sql(query, conn)
        
        df_risk['suspicious_ratio'] = df_risk['suspicious_trans'] / df_risk['total_trans']
        
        risk_patterns = ['Cheque', 'Efectivo', 'Money Order']
        df_risk['risk_payment_formats'] = df_risk['payment_formats'].apply(
            lambda x: sum(1 for pattern in risk_patterns if pattern in str(x))
        )
        
        df_risk['risk_score'] = df_risk.apply(calculate_risk_score, axis=1)
        
        df_risk[['risk_level', 'risk_icon', 'risk_color']] = df_risk['risk_score'].apply(
            lambda x: pd.Series(get_risk_level(x))
        )
    
    conn.close()
    
    st.subheader("📊 Resumen de Riesgo")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        alto_riesgo = len(df_risk[df_risk['risk_level'] == 'Alto Riesgo'])
        st.metric("🔴 Clientes Alto Riesgo", f"{alto_riesgo:,}")
    
    with col2:
        medio_riesgo = len(df_risk[df_risk['risk_level'] == 'Riesgo Medio'])
        st.metric("🟡 Clientes Riesgo Medio", f"{medio_riesgo:,}")
    
    with col3:
        bajo_riesgo = len(df_risk[df_risk['risk_level'] == 'Bajo Riesgo'])
        st.metric("🟢 Clientes Bajo Riesgo", f"{bajo_riesgo:,}")
    
    with col4:
        score_promedio = df_risk['risk_score'].mean()
        st.metric("📊 Score de Riesgo Promedio", f"{score_promedio:.1f}/100")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Distribución de Niveles de Riesgo")
        risk_counts = df_risk['risk_level'].value_counts()
        fig = px.pie(
            values=risk_counts.values, 
            names=risk_counts.index,
            color=risk_counts.index,
            color_discrete_map={
                'Alto Riesgo': '#ff4444',
                'Riesgo Medio': '#ffaa00',
                'Bajo Riesgo': '#00ff9d'
            },
            title="Porcentaje de clientes por nivel de riesgo"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📊 Score de Riesgo - Distribución")
        fig = px.histogram(
            df_risk, 
            x='risk_score', 
            nbins=20,
            title="Distribución de scores de riesgo",
            labels={'risk_score': 'Score de Riesgo', 'count': 'Número de clientes'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    st.subheader("🔴 Top 20 Clientes de Alto Riesgo")
    
    top_risk = df_risk[df_risk['risk_level'] == 'Alto Riesgo'].nlargest(20, 'risk_score')[
        ['Account', 'risk_score', 'risk_level', 'suspicious_trans', 'total_trans', 
         'suspicious_ratio', 'avg_amount', 'total_amount', 'payment_formats']
    ]
    
    top_risk.columns = ['Cuenta', 'Score', 'Nivel', 'Alertas', 'Total Transacciones', 
                        'Tasa Sospecha', 'Monto Promedio', 'Monto Total', 'Formatos de Pago']
    
    st.dataframe(
        top_risk,
        use_container_width=True,
        column_config={
            "Score": st.column_config.ProgressColumn("Score", format="%.0f", min_value=0, max_value=100),
            "Monto Promedio": st.column_config.NumberColumn("Monto Promedio", format="$%.2f"),
            "Monto Total": st.column_config.NumberColumn("Monto Total", format="$%.2f"),
            "Tasa Sospecha": st.column_config.NumberColumn("Tasa Sospecha", format="%.2f%%"),
        }
    )
    
    st.markdown("---")
    
    st.subheader("📋 Factores de Riesgo Considerados")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        **💰 Transacciones Sospechosas** (40 pts)
        - >10%: +40 pts
        - >5%: +30 pts
        - >1%: +20 pts
        - >0%: +10 pts
        """)
    
    with col2:
        st.markdown("""
        **💵 Monto Promedio** (25 pts)
        - >$50k: +25 pts
        - >$20k: +18 pts
        - >$10k: +12 pts
        - >$5k: +6 pts
        """)
    
    with col3:
        st.markdown("""
        **📊 Frecuencia** (20 pts)
        - >1000 tx: +20 pts
        - >500 tx: +14 pts
        - >100 tx: +8 pts
        - >50 tx: +4 pts
        """)
    
    with col4:
        st.markdown("""
        **⚠️ Formatos Riesgosos** (15 pts)
        - Cheque: +5 pts
        - Efectivo: +5 pts
        - Money Order: +5 pts
        """)
    
    st.markdown("---")
    
    st.subheader("🔍 Consultar Score por Cuenta")
    
    account_input = st.text_input("Ingresá el número de cuenta (ej: 8000EBD30)")
    
    if account_input:
        account_data = df_risk[df_risk['Account'] == account_input]
        
        if not account_data.empty:
            row = account_data.iloc[0]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div style="background: #1a1a2e; border-radius: 10px; padding: 20px; text-align: center;">
                    <div style="font-size: 14px; color: #888;">Score de Riesgo</div>
                    <div style="font-size: 48px; font-weight: bold; color: {row['risk_color']}">{row['risk_score']:.0f}</div>
                    <div style="font-size: 18px; color: {row['risk_color']}">{row['risk_level']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style="background: #1a1a2e; border-radius: 10px; padding: 20px; text-align: center;">
                    <div style="font-size: 14px; color: #888;">Transacciones</div>
                    <div style="font-size: 32px; font-weight: bold;">{int(row['total_trans']):,}</div>
                    <div style="font-size: 12px; color: #ff4444;">Alertas: {int(row['suspicious_trans'])}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div style="background: #1a1a2e; border-radius: 10px; padding: 20px; text-align: center;">
                    <div style="font-size: 14px; color: #888;">Monto Total</div>
                    <div style="font-size: 32px; font-weight: bold;">${row['total_amount']:,.2f}</div>
                    <div style="font-size: 12px; color: #888;">Promedio: ${row['avg_amount']:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown(f"**📋 Formatos de pago utilizados:** {row['payment_formats']}")
            
        else:
            st.warning(f"No se encontró la cuenta {account_input}")
    
    st.caption(f"📅 Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total de cuentas analizadas: {len(df_risk):,}")

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