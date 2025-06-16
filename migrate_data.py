# migrate_data.py
import sqlite3
import pandas as pd
from sqlalchemy import create_engine
import os

print("Starting data migration...")

# --- 1. Extract from SQLite file in the current directory ---
sqlite_conn = sqlite3.connect('nwh_doctors.db')
table_names = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", sqlite_conn)

# --- 2. Connect to Cloud SQL via the Auth Proxy ---
DB_USER = "postgres"
DB_PASS = "root" # <-- IMPORTANT: REPLACE THIS
DB_NAME = "providers"
DB_HOST = "127.0.0.1" # The Auth Proxy listens on localhost
DB_PORT = "5432"

engine = create_engine(f'postgresql+pg8000://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

# --- 3. Loop through all tables and migrate them ---
for table_name in table_names['name'].tolist():
    if table_name.startswith('sqlite_'):
        print(f"Skipping system table: {table_name}")
        continue
    
    print(f"Migrating table: {table_name}...")
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", sqlite_conn)
    
    # Load data into new table in Cloud SQL. Use 'replace' to ensure clean runs.
    df.to_sql(table_name, engine, if_exists='replace', index=False)
    print(f"Successfully migrated {table_name}.")

sqlite_conn.close()
print("Data migration complete.")