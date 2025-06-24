from database import SessionLocal
from models import Azienda, Utente

db = SessionLocal()

# Aggiungi una azienda
azienda = Azienda(nome="Acme Srl", email="info@acme.it", descrizione="Azienda di esempio.")
db.add(azienda)
db.commit()
db.refresh(azienda)

# Aggiungi un utente collegato all'azienda
utente = Utente(nome="Mario Rossi", email="mario@acme.it", password="1234", azienda_id=azienda.id)
db.add(utente)
db.commit()
db.refresh(utente)

print("Azienda e utente aggiunti!")
db.close()