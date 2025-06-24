from database import engine, Base
import models  # importa il tuo file models.py (deve essere nella stessa cartella)


import os
print("Sto creando il database in:", os.getcwd())
# Crea tutte le tabelle nel database
Base.metadata.create_all(bind=engine)
print("Database e tabelle create!")