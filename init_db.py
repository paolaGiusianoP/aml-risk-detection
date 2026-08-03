import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'aml_risk_db',
    'user': 'postgres',
    'password': 'postgres123'
}

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

# Crear tabla de casos
cursor.execute("""
    CREATE TABLE IF NOT EXISTS cases (
        case_id SERIAL PRIMARY KEY,
        account VARCHAR(50),
        transaction_id VARCHAR(50),
        alert_date TIMESTAMP DEFAULT NOW(),
        amount DECIMAL(15,2),
        payment_format VARCHAR(50),
        status VARCHAR(20) DEFAULT 'Abierto',
        severity VARCHAR(20),
        assigned_to VARCHAR(100) DEFAULT 'Analista AML',
        analyst_notes TEXT,
        resolution_date TIMESTAMP,
        created_at TIMESTAMP DEFAULT NOW()
    )
""")

# Crear tabla de comentarios
cursor.execute("""
    CREATE TABLE IF NOT EXISTS case_comments (
        comment_id SERIAL PRIMARY KEY,
        case_id INTEGER REFERENCES cases(case_id) ON DELETE CASCADE,
        comment TEXT,
        created_by VARCHAR(100),
        created_at TIMESTAMP DEFAULT NOW()
    )
""")

cursor.execute("SELECT COUNT(*) FROM cases")
count = cursor.fetchone()[0]

if count == 0:
    casos_ejemplo = [
        ("8000EBD30", 3697.34, "Reinvestment", "Medio"),
        ("8000F4580", 14675.57, "Transferencia", "Alto"),
        ("8000F5030", 2806.97, "Cheque", "Bajo"),
        ("8000F5200", 36682.97, "Reinvestment", "Alto"),
        ("8043A0FB0", 12500.00, "Transferencia", "Medio"),
    ]
    
    for account, amount, payment_format, severity in casos_ejemplo:
        cursor.execute("""
            INSERT INTO cases (account, amount, payment_format, severity, status, alert_date)
            VALUES (%s, %s, %s, %s, 'Abierto', NOW())
        """, (account, amount, payment_format, severity))
    

conn.commit()

# Verificar
cursor.execute("SELECT COUNT(*) FROM cases")
final_count = cursor.fetchone()[0]

cursor.close()
conn.close()