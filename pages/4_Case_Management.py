import streamlit as st
import pandas as pd
import os
import psycopg2
from datetime import datetime

st.set_page_config(page_title="Case Management", page_icon="📋", layout="wide")

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

st.title("Case Management")
st.markdown("Gestión de casos de investigación de alertas AML")
st.markdown("---")

def create_case_from_alert(account, amount, payment_format, severity):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO cases (account, amount, payment_format, severity, status, alert_date)
        VALUES (%s, %s, %s, %s, 'Abierto', NOW())
        RETURNING case_id
    """, (account, amount, payment_format, severity))
    
    case_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return case_id

def update_case_status(case_id, new_status, notes=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    if notes:
        cursor.execute("""
            UPDATE cases 
            SET status = %s, analyst_notes = %s, resolution_date = CASE WHEN %s = 'Cerrado' THEN NOW() ELSE NULL END
            WHERE case_id = %s
        """, (new_status, notes, new_status, case_id))
    else:
        cursor.execute("""
            UPDATE cases 
            SET status = %s, resolution_date = CASE WHEN %s = 'Cerrado' THEN NOW() ELSE NULL END
            WHERE case_id = %s
        """, (new_status, new_status, case_id))
    
    conn.commit()
    cursor.close()
    conn.close()

def add_comment(case_id, comment):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO case_comments (case_id, comment, created_by)
        VALUES (%s, %s, %s)
    """, (case_id, comment, "Analista AML"))
    
    conn.commit()
    cursor.close()
    conn.close()

def get_case_comments(case_id):
    conn = get_connection()
    query = """
        SELECT comment, created_by, created_at 
        FROM case_comments 
        WHERE case_id = %s 
        ORDER BY created_at DESC
    """
    df = pd.read_sql(query, conn, params=(case_id,))
    conn.close()
    return df

try:
    with st.sidebar:
        st.markdown("### 📊 Estadísticas de Casos")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM cases")
        total_cases = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM cases WHERE status = 'Abierto'")
        open_cases = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM cases WHERE status = 'En revisión'")
        review_cases = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM cases WHERE status = 'Cerrado'")
        closed_cases = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM cases WHERE status = 'Escalado'")
        escalated_cases = cursor.fetchone()[0]
        
        conn.close()
        
        st.metric("📋 Total Casos", total_cases)
        st.metric("🟢 Abiertos", open_cases)
        st.metric("🟡 En revisión", review_cases)
        st.metric("🔴 Escalados", escalated_cases)
        st.metric("✅ Cerrados", closed_cases)

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Casos Abiertos", "➕ Crear Nuevo Caso", "🔍 Buscar Caso", "📊 Resumen"])

    with tab1:
        st.subheader("📋 Casos Activos")
        
        conn = get_connection()
        query = """
            SELECT case_id, account, amount, payment_format, severity, status, alert_date, analyst_notes
            FROM cases 
            WHERE status IN ('Abierto', 'En revisión')
            ORDER BY alert_date DESC
        """
        df_cases = pd.read_sql(query, conn)
        conn.close()
        
        if not df_cases.empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_severity = st.selectbox("Filtrar por severidad", ["Todos", "Alto", "Medio", "Bajo"])
            with col2:
                filter_status = st.selectbox("Filtrar por estado", ["Todos", "Abierto", "En revisión"])
            
            if filter_severity != "Todos":
                df_cases = df_cases[df_cases['severity'] == filter_severity]
            if filter_status != "Todos":
                df_cases = df_cases[df_cases['status'] == filter_status]
            
            for _, case in df_cases.iterrows():
                severity_color = {"Alto": "🔴", "Medio": "🟡", "Bajo": "🟢"}.get(case['severity'], "⚪")
                
                with st.expander(f"{severity_color} Caso #{case['case_id']} - Cuenta: {case['account']} - {case['status']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**💰 Monto:** ${case['amount']:,.2f}")
                        st.markdown(f"**📅 Fecha alerta:** {case['alert_date']}")
                        st.markdown(f"**📋 Formato:** {case['payment_format']}")
                    
                    with col2:
                        st.markdown(f"**⚠️ Severidad:** {case['severity']}")
                        st.markdown(f"**📌 Estado:** {case['status']}")
                    
                    st.markdown("---")
                    
                    col_action1, col_action2, col_action3, col_action4 = st.columns(4)
                    
                    with col_action1:
                        if st.button(f"✅ Aprobar", key=f"approve_{case['case_id']}"):
                            update_case_status(case['case_id'], "Cerrado", "Caso aprobado sin actividad sospechosa")
                            st.success(f"Caso #{case['case_id']} cerrado")
                            st.rerun()
                    
                    with col_action2:
                        if st.button(f"⚠️ Escalar", key=f"escalate_{case['case_id']}"):
                            update_case_status(case['case_id'], "Escalado", "Caso escalado para revisión superior")
                            st.warning(f"Caso #{case['case_id']} escalado")
                            st.rerun()
                    
                    with col_action3:
                        if st.button(f"🔄 En revisión", key=f"review_{case['case_id']}"):
                            update_case_status(case['case_id'], "En revisión")
                            st.info(f"Caso #{case['case_id']} en revisión")
                            st.rerun()
                    
                    with col_action4:
                        with st.popover(f"📝 Agregar nota", key=f"note_{case['case_id']}"):
                            note = st.text_area("Nota", key=f"note_text_{case['case_id']}")
                            if st.button("Guardar nota", key=f"save_note_{case['case_id']}"):
                                if note:
                                    add_comment(case['case_id'], note)
                                    st.success("Nota agregada")
                                    st.rerun()
                    
                    comments_df = get_case_comments(case['case_id'])
                    if not comments_df.empty:
                        st.markdown("**Historial de comentarios:**")
                        for _, comment in comments_df.iterrows():
                            st.caption(f" {comment['comment']} - *{comment['created_by']} - {comment['created_at']}*")
        else:
            st.info("No hay casos activos")

    with tab2:
        st.subheader("➕ Crear Nuevo Caso desde Alerta")
        
        conn = get_connection()
        query_alerts = """
            SELECT "Account", "Amount_Paid", "Payment_Format"
            FROM transactions 
            WHERE "Is_Laundering" = 1 
            ORDER BY "Timestamp" DESC 
            LIMIT 20
        """
        df_alerts = pd.read_sql(query_alerts, conn)
        conn.close()
        
        if not df_alerts.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                selected_alert = st.selectbox(
                    "Seleccionar alerta para crear caso",
                    df_alerts.index,
                    format_func=lambda x: f"Cuenta: {df_alerts.loc[x, 'Account']} - ${df_alerts.loc[x, 'Amount_Paid']:,.2f}"
                )
            
            with col2:
                severity = st.selectbox("Severidad", ["Alto", "Medio", "Bajo"])
            
            if st.button("📋 Crear Caso", type="primary"):
                alert = df_alerts.loc[selected_alert]
                case_id = create_case_from_alert(
                    alert['Account'],
                    alert['Amount_Paid'],
                    alert['Payment_Format'],
                    severity
                )
                st.success(f"Caso #{case_id} creado correctamente")
                st.rerun()
        else:
            st.info("No hay alertas disponibles para crear casos")

    with tab3:
        st.subheader(" Buscar Caso por ID")
        
        search_id = st.number_input("Número de caso", min_value=1, step=1)
        
        if search_id:
            conn = get_connection()
            query = "SELECT * FROM cases WHERE case_id = %s"
            df_case = pd.read_sql(query, conn, params=(search_id,))
            conn.close()
            
            if not df_case.empty:
                case = df_case.iloc[0]
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"**📋 Caso ID:** {case['case_id']}")
                    st.markdown(f"**🏦 Cuenta:** {case['account']}")
                    st.markdown(f"**💰 Monto:** ${case['amount']:,.2f}")
                
                with col2:
                    st.markdown(f"**⚠️ Severidad:** {case['severity']}")
                    st.markdown(f"**📌 Estado:** {case['status']}")
                    st.markdown(f"**📅 Fecha:** {case['alert_date']}")
                
                with col3:
                    if case['status'] == 'Cerrado':
                        st.markdown(f"**✅ Resuelto:** {case['resolution_date']}")
                
                st.markdown("---")
                st.subheader("⚙️ Acciones")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("✅ Aprobar", key="search_approve"):
                        update_case_status(search_id, "Cerrado", "Caso aprobado")
                        st.success(f"Caso #{search_id} cerrado")
                        st.rerun()
                
                with col2:
                    if st.button("⚠️ Escalar", key="search_escalate"):
                        update_case_status(search_id, "Escalado", "Caso escalado")
                        st.warning(f"Caso #{search_id} escalado")
                        st.rerun()
                
                st.markdown("---")
                st.subheader("📝 Comentarios")
                
                comments_df = get_case_comments(search_id)
                if not comments_df.empty:
                    for _, comment in comments_df.iterrows():
                        st.caption(f"🗨️ {comment['comment']} - *{comment['created_by']} - {comment['created_at']}*")
                
                new_comment = st.text_area("Agregar comentario", key="search_comment")
                if st.button("Guardar comentario", key="search_save_comment"):
                    if new_comment:
                        add_comment(search_id, new_comment)
                        st.success("Comentario agregado")
                        st.rerun()
            else:
                st.error(f"No se encontró el caso #{search_id}")

    with tab4:
        st.subheader("📊 Resumen de Casos")
        
        conn = get_connection()
        
        query_severity = """
            SELECT severity, COUNT(*) as count 
            FROM cases 
            GROUP BY severity
        """
        df_severity = pd.read_sql(query_severity, conn)
        
        query_status = """
            SELECT status, COUNT(*) as count 
            FROM cases 
            GROUP BY status
        """
        df_status = pd.read_sql(query_status, conn)
        
        query_monthly = """
            SELECT DATE_TRUNC('month', alert_date) as month, COUNT(*) as count 
            FROM cases 
            GROUP BY DATE_TRUNC('month', alert_date)
            ORDER BY month DESC
            LIMIT 6
        """
        df_monthly = pd.read_sql(query_monthly, conn)
        
        conn.close()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Por severidad**")
            st.dataframe(df_severity, use_container_width=True)
        
        with col2:
            st.markdown("**Por estado**")
            st.dataframe(df_status, use_container_width=True)
        
        if not df_monthly.empty:
            st.markdown("**Evolución mensual**")
            st.dataframe(df_monthly, use_container_width=True)

    st.caption(f"📅 Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

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