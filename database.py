# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Stringa di connessione per SQLite.
# Il database sarà un file chiamato 'test.db' nella directory corrente del progetto.
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Creazione dell'engine di SQLAlchemy.
# connect_args={"check_same_thread": False} è necessario solo per SQLite
# per permettere l'uso con FastAPI che opera in modo asincrono.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# SessionLocal sarà la classe che useremo per creare le sessioni del database.
# Ogni istanza di SessionLocal sarà una sessione di database.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base è una classe base da cui tutti i nostri modelli ORM (tabelle del database) erediteranno.
Base = declarative_base()

# Funzione di utilità per ottenere una sessione del database (opzionale qui,
# ma spesso messa in database.py o in main.py come dependency).
# L'hai già definita in main.py, quindi qui non è strettamente necessaria,
# ma la lascio commentata come riferimento se volessi centralizzarla.
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()