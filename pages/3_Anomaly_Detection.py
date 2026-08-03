import streamlit as st
import pandas as pd
import psycopg2
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, roc_auc_score, roc_curve
from sklearn.utils import resample
from xgboost import XGBClassifier
import warnings
import os
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Anomaly Detection", page_icon="⚠️", layout="wide")

def get_connection():
    # Primero intentar con secrets (Render)
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

st.title("Anomaly Detection")
st.markdown("Detección de anomalías usando reglas de negocio y Machine Learning")
st.markdown("---")

try:
    conn = get_connection()

    query_data = '''
        SELECT 
            "Amount_Paid" as amount,
            "Payment_Format",
            EXTRACT(HOUR FROM CAST("Timestamp" AS TIMESTAMP)) as hour,
            EXTRACT(DOW FROM CAST("Timestamp" AS TIMESTAMP)) as day_of_week,
            "Is_Laundering" as target
        FROM transactions
        LIMIT 500000
    '''

    df = pd.read_sql(query_data, conn)
    conn.close()

    st.success(f"Datos cargados: {len(df):,} transacciones")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total transacciones", f"{len(df):,}")
    with col2:
        suspicious = df['target'].sum()
        st.metric("Transacciones sospechosas", f"{suspicious:,}", delta=f"{suspicious/len(df)*100:.4f}%")
    with col3:
        avg_amount = df['amount'].mean()
        st.metric("Monto promedio", f"${avg_amount:,.2f}")

    st.markdown("---")

    st.subheader("📋 Reglas de Negocio para Detección de Anomalías")

    col1, col2 = st.columns(2)

    with col1:
        high_amount_threshold = st.slider("💰 Monto elevado (USD)", 10000, 100000, 50000, step=5000)
        high_amount_alerts = len(df[df['amount'] > high_amount_threshold])
        high_amount_suspicious = len(df[(df['amount'] > high_amount_threshold) & (df['target'] == 1)])
        precision_high = high_amount_suspicious / high_amount_alerts * 100 if high_amount_alerts > 0 else 0
        
        st.markdown(f"""
        **Regla 1: Transacciones de alto monto**
        - Umbral: > ${high_amount_threshold:,}
        - Alertas generadas: {high_amount_alerts:,}
        - Verdaderos positivos: {high_amount_suspicious:,}
        - Precisión: {precision_high:.2f}%
        """)

    with col2:
        unusual_hours = st.multiselect("🕐 Horarios inusuales", list(range(24)), default=[0,1,2,3,4,5,22,23])
        unusual_hours_alerts = len(df[df['hour'].isin(unusual_hours)])
        unusual_hours_suspicious = len(df[(df['hour'].isin(unusual_hours)) & (df['target'] == 1)])
        precision_hours = unusual_hours_suspicious / unusual_hours_alerts * 100 if unusual_hours_alerts > 0 else 0
        
        st.markdown(f"""
        **Regla 2: Transacciones en horarios inusuales**
        - Horas: {unusual_hours}
        - Alertas generadas: {unusual_hours_alerts:,}
        - Verdaderos positivos: {unusual_hours_suspicious:,}
        - Precisión: {precision_hours:.2f}%
        """)

    st.markdown("---")

    st.subheader("🤖 Machine Learning - Predicción de Fraude")

    df_ml = df.copy()

    payment_format_dummies = pd.get_dummies(df_ml['Payment_Format'], prefix='format')
    df_ml = pd.concat([df_ml, payment_format_dummies], axis=1)

    df_ml['amount_log'] = np.log1p(df_ml['amount'])
    df_ml['amount_squared'] = df_ml['amount'] ** 2
    df_ml['is_weekend'] = df_ml['day_of_week'].isin([5, 6]).astype(int)
    df_ml['is_night'] = df_ml['hour'].isin([0,1,2,3,4,5,22,23]).astype(int)

    feature_cols = ['amount', 'amount_log', 'amount_squared', 'hour', 'day_of_week', 
                    'is_weekend', 'is_night'] + list(payment_format_dummies.columns)

    X = df_ml[feature_cols]
    y = df_ml['target']

    X_majority = X[y == 0]
    X_minority = X[y == 1]
    y_majority = y[y == 0]
    y_minority = y[y == 1]

    if len(X_minority) > 0:
        n_samples = min(len(X_minority) * 10, len(X_majority))
        X_majority_downsampled, y_majority_downsampled = resample(
            X_majority, y_majority,
            replace=False,
            n_samples=n_samples,
            random_state=42
        )
        
        X_balanced = pd.concat([X_majority_downsampled, X_minority])
        y_balanced = pd.concat([y_majority_downsampled, y_minority])
        
        st.info(f"📊 Dataset balanceado: {len(X_balanced):,} transacciones")
        
        st.subheader("Comparación de Modelos")
        
        X_train, X_test, y_train, y_test = train_test_split(X_balanced, y_balanced, test_size=0.3, random_state=42)
        
        models = {
            "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
            "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
            "XGBoost": XGBClassifier(n_estimators=100, random_state=42, use_label_encoder=False, eval_metric='logloss')
        }
        
        results = {}
        
        if st.button("Entrenar Modelos de Machine Learning", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, (name, model) in enumerate(models.items()):
                status_text.text(f"Entrenando {name}...")
                model.fit(X_train, y_train)
                
                y_pred = model.predict(X_test)
                y_pred_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else y_pred
                
                results[name] = {
                    "accuracy": accuracy_score(y_test, y_pred),
                    "precision": precision_score(y_test, y_pred),
                    "recall": recall_score(y_test, y_pred),
                    "f1": f1_score(y_test, y_pred),
                    "roc_auc": roc_auc_score(y_test, y_pred_proba) if hasattr(model, "predict_proba") else 0,
                    "y_pred": y_pred,
                    "y_pred_proba": y_pred_proba
                }
                progress_bar.progress((i + 1) / len(models))
            
            status_text.text("Entrenamiento completado!")
            progress_bar.empty()
            
            st.markdown("---")
            st.subheader("📊 Comparación de Rendimiento")
            
            results_df = pd.DataFrame({
                name: {
                    "Accuracy": f"{results[name]['accuracy']:.4f}",
                    "Precision": f"{results[name]['precision']:.4f}",
                    "Recall": f"{results[name]['recall']:.4f}",
                    "F1-Score": f"{results[name]['f1']:.4f}",
                    "ROC-AUC": f"{results[name]['roc_auc']:.4f}"
                }
                for name in models.keys()
            }).T
            
            st.dataframe(results_df, use_container_width=True)
            
            st.subheader("📈 Comparativa Visual")
            
            metrics = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']
            fig_data = []
            
            for name in models.keys():
                for metric in metrics:
                    fig_data.append({
                        'Modelo': name,
                        'Métrica': metric.upper(),
                        'Valor': results[name][metric]
                    })
            
            df_plot = pd.DataFrame(fig_data)
            fig = px.bar(df_plot, x='Modelo', y='Valor', color='Métrica', 
                         barmode='group', title="Comparación de Métricas por Modelo",
                         color_discrete_sequence=px.colors.qualitative.Set1)
            st.plotly_chart(fig, use_container_width=True)
            
            best_model = max(results.keys(), key=lambda x: results[x]['f1'])
            st.success(f"🏆 **Mejor modelo: {best_model}** (F1-Score: {results[best_model]['f1']:.4f})")
            
            st.subheader(f"📋 Matriz de Confusión - {best_model}")
            cm = confusion_matrix(y_test, results[best_model]['y_pred'])
            fig_cm = px.imshow(cm, text_auto=True, 
                                labels=dict(x="Predicción", y="Real", color="Count"),
                                x=["Normal", "Sospechosa"],
                                y=["Normal", "Sospechosa"],
                                color_continuous_scale="Reds")
            st.plotly_chart(fig_cm, use_container_width=True)
            
            st.subheader(f"📈 Curva ROC - {best_model}")
            fpr, tpr, _ = roc_curve(y_test, results[best_model]['y_pred_proba'])
            fig_roc = go.Figure()
            fig_roc.add_trace(go.Scatter(x=fpr, y=tpr, mode='lines', name=f'{best_model} (AUC = {results[best_model]["roc_auc"]:.4f})'))
            fig_roc.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode='lines', name='Clasificador Aleatorio', line=dict(dash='dash')))
            fig_roc.update_layout(title="Curva ROC", xaxis_title="Tasa de Falsos Positivos", yaxis_title="Tasa de Verdaderos Positivos")
            st.plotly_chart(fig_roc, use_container_width=True)
            
            if best_model in ["Random Forest", "XGBoost"]:
                st.subheader(f"Importancia de Características - {best_model}")
                best_model_obj = models[best_model]
                best_model_obj.fit(X_train, y_train)
                feature_importance = best_model_obj.feature_importances_
                
                importance_df = pd.DataFrame({
                    'Característica': feature_cols,
                    'Importancia': feature_importance
                }).sort_values('Importancia', ascending=False).head(10)
                
                fig_imp = px.bar(importance_df, x='Importancia', y='Característica', orientation='h',
                                 title="Top 10 Características más Importantes")
                st.plotly_chart(fig_imp, use_container_width=True)
    else:
        st.error("No hay suficientes transacciones sospechosas para entrenar modelos")

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