import pandas as pd
import psycopg2
from sqlalchemy import create_engine

# Configuración de conexión
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'aml_risk_db',
    'user': 'postgres',
    'password': 'postgres123'
}


DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
engine = create_engine(DATABASE_URL)

# Cargar CSV
accounts = pd.read_csv('data/raw/HI-Small_accounts.csv')
trans = pd.read_csv('data/raw/HI-Small_Trans.csv')

accounts.columns = [col.replace(' ', '_') for col in accounts.columns]
trans.columns = [col.replace(' ', '_') for col in trans.columns]

from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS accounts CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS transactions CASCADE"))
    conn.commit()

for col in trans.select_dtypes(include=['object']).columns:
    trans[col] = trans[col].astype(str).str[:255] 

for col in accounts.select_dtypes(include=['object']).columns:
    accounts[col] = accounts[col].astype(str).str[:255]


# Cargar a PostgreSQL
accounts.to_sql('accounts', engine, if_exists='replace', index=False, method='multi')

trans.to_sql('transactions', engine, if_exists='replace', index=False, chunksize=50000)

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM accounts")
accounts_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM transactions")
trans_count = cursor.fetchone()[0]

print(f"Accounts en PostgreSQL: {accounts_count:,}")
print(f"Transactions en PostgreSQL: {trans_count:,}")

cursor.execute("SELECT * FROM transactions LIMIT 5")
sample = cursor.fetchall()
for row in sample:
    print(row)

cursor.close()
conn.close()