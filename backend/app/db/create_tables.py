from app.db.session import engine
from app.db.base import Base

def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas com sucesso!")

if __name__ == "__main__":
    create_tables()