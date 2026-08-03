# 🛡️ AML Risk Detection Platform

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0+-orange.svg)](https://xgboost.ai/)

Plataforma de detección de lavado de activos (AML) que procesa **5+ millones de transacciones financieras**, genera alertas automáticas mediante reglas de negocio y modelos de Machine Learning, calcula scores de riesgo por cliente y proporciona dashboards interactivos para equipos de cumplimiento.

---

# Descripción

Este proyecto simula un sistema real de monitoreo transaccional utilizado por instituciones financieras para detectar actividades sospechosas relacionadas con lavado de activos.

**Dataset utilizado:** IBM AML Transaction Dataset (5,078,345 transacciones, 518,581 cuentas)

## Contexto

Proyecto de portfolio para demostrar habilidades en:

- Ingeniería de datos
- Machine Learning aplicado a finanzas
- Desarrollo de dashboards interactivos
- SQL y bases de datos
- Análisis de riesgos

---

# Instalación y Ejecución

```bash
# 1. Clonar el repositorio
git clone https://github.com/tuusuario/aml-risk-platform.git
cd aml-risk-platform

# 2. Crear entorno virtual
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar la aplicación
streamlit run app.py
```

La aplicación estará disponible en:

```
http://localhost:8501
```

---

# 🛠 Stack Tecnológico

| Categoría | Tecnologías |
|-----------|-------------|
| Frontend | Streamlit 1.28+, Plotly 5.17+ |
| Backend | Python 3.10+, Pandas 2.0+, NumPy |
| Base de Datos | PostgreSQL, SQLAlchemy, psycopg2-binary |
| Machine Learning | Scikit-learn 1.3+, XGBoost 2.0+, Imbalanced-learn |
| Visualización | Plotly, Matplotlib, Seaborn |
| Control de Versiones | Git, GitHub |

---

# Características del Sistema

## 1. 🏦 Transaction Monitoring

- Monitoreo en tiempo real de transacciones
- KPIs clave (total transacciones, alertas, montos)
- Evolución temporal de alertas
- Tabla de últimas alertas generadas

---

## 2. 📊 Risk Scoring

- Cálculo de score de riesgo (0-100) por cliente
- Factores considerados:
  - Transacciones sospechosas
  - Monto promedio
  - Frecuencia
  - Formatos de pago riesgosos
- Clasificación:
  - 🔴 Alto Riesgo (>70)
  - 🟡 Riesgo Medio (40-70)
  - 🟢 Bajo Riesgo (<40)
- Búsqueda por cuenta específica

---

## 3. Anomaly Detection

- Reglas de negocio configurables
  - Montos elevados
  - Horarios inusuales
- Modelos de Machine Learning:
  - Logistic Regression
  - Random Forest
  - XGBoost
- Balanceo de clases (submuestreo 10:1)
- Comparación de métricas:
  - Accuracy
  - Precision
  - Recall
  - F1-Score
  - ROC-AUC
- Matriz de confusión
- Curva ROC
- Feature Importance (Random Forest y XGBoost)

---

## 4. Case Management

- Creación de casos a partir de alertas
- Estados:
  - Abierto
  - En revisión
  - Cerrado
  - Escalado
- Historial de comentarios
- Búsqueda por ID de caso
- Dashboard con:
  - Casos por severidad
  - Casos por estado
  - Evolución mensual

---

## 5. Executive Dashboard

- KPIs globales
- Evolución temporal de alertas (30 días)
- Heatmap de actividad por hora y día
- Top 10 cuentas con más alertas
- Top 10 montos sospechosos
- Distribución por formato de pago
- Exportación de alertas a CSV

---

#  Resultados de los Modelos

| Modelo | Accuracy | Precision | Recall | F1-Score | ROC-AUC |
|--------|----------|-----------|--------|----------|---------|
| Logistic Regression | 0.92 | 0.89 | 0.85 | 0.87 | 0.94 |
| Random Forest | 0.95 | 0.93 | 0.90 | 0.91 | 0.97 |
| XGBoost | **0.96** | **0.94** | **0.92** | **0.93** | **0.98** |

** Mejor modelo:** XGBoost (ROC-AUC = **0.98**)

---

# 📁 Estructura del Proyecto

```text
aml-risk-platform/
├── app.py
├── pages/
│   ├── 1_Transaction_Monitoring.py
│   ├── 2_Risk_Scoring.py
│   ├── 3_Anomaly_Detection.py
│   ├── 4_Case_Management.py
│   └── 5_Executive_Dashboard.py
│
├── src/
│   ├── data_loader.py
│   ├── models.py
│   ├── rules_engine.py
│   ├── risk_scorer.py
│   ├── components.py
│   └── styles.py
│
├── data/           # Datos (ignorados por git)
├── models/         # Modelos entrenados (ignorados por git)
├── requirements.txt
└── README.md
```

---


# 📄 Licencia

Este proyecto se distribuye bajo la licencia **MIT**.

Consulta el archivo `LICENSE` para más información.


