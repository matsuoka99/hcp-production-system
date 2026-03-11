from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql+psycopg://postgres:v2612hcp@localhost:5432/hcp_production_system"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("SELECT version();"))
    row = result.fetchone()
    print("Conexão OK!")
    print(row[0])