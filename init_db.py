from database import SessionLocal
import models

def init():
    db = SessionLocal()
    # Esempio: aggiungi una azienda
    azienda = models.Azienda(nome="Test", email="test@azienda.com")
    db.add(azienda)
    db.commit()
    db.close()

if __name__ == "__main__":
    init()