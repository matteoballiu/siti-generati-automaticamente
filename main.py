# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List 
# Importa i tuoi moduli locali
import models 
import schemas 
import crud 
from database import SessionLocal, engine # Da database_py_sqlite_config_v2

# Crea tutte le tabelle definite in models.py nel database all'avvio dell'applicazione.
# Questa operazione è idempotente (non farà nulla se le tabelle esistono già).
try:
    print("INFO:     Tentativo di creazione/controllo tabelle del database...")
    models.Base.metadata.create_all(bind=engine)
    print("INFO:     Tabelle controllate/create con successo.")
except Exception as e:
    print(f"ERRORE: Errore durante la creazione delle tabelle: {e}")

app = FastAPI(
    title="API Agente Virtuale (Ricostruzione)",
    description="API per la gestione dell'anamnesi clienti e l'automazione di processi.",
    version="0.3.1" # Aggiorna la versione se lo ritieni opportuno
)

# Dependency per ottenere la sessione del database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Endpoint per Aziende ---
@app.post("/aziende/", response_model=schemas.Azienda, tags=["Aziende"], status_code=status.HTTP_201_CREATED)
def crea_azienda(azienda: schemas.AziendaCreate, db: Session = Depends(get_db)):
    # La gestione dell'IntegrityError per email duplicata è in crud.create_azienda
    return crud.create_azienda(db=db, azienda=azienda)

@app.get("/aziende/", response_model=List[schemas.Azienda], tags=["Aziende"])
def lista_aziende(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)): 
    aziende = crud.get_aziende(db=db, skip=skip, limit=limit)
    return aziende

@app.get("/aziende/{azienda_id}", response_model=schemas.Azienda, tags=["Aziende"])
def leggi_azienda(azienda_id: int, db: Session = Depends(get_db)):
    db_azienda = crud.get_azienda(db=db, azienda_id=azienda_id)
    if db_azienda is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Azienda non trovata")
    return db_azienda

# --- Endpoint per Utenti ---
@app.post("/utenti/", response_model=schemas.Utente, tags=["Utenti"], status_code=status.HTTP_201_CREATED)
def crea_utente(utente: schemas.UtenteCreate, db: Session = Depends(get_db)):
    # La gestione dell'IntegrityError e l'hashing della password dovrebbero essere in crud.create_utente
    return crud.create_utente(db=db, utente=utente)

@app.get("/utenti/{utente_id}", response_model=schemas.Utente, tags=["Utenti"])
def leggi_utente(utente_id: int, db: Session = Depends(get_db)):
    db_utente = crud.get_utente(db=db, utente_id=utente_id)
    if db_utente is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato")
    return db_utente

@app.get("/utenti/", response_model=List[schemas.Utente], tags=["Utenti"])
def leggi_utenti(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    utenti = crud.get_utenti(db=db, skip=skip, limit=limit)
    return utenti

# --- Endpoint per Richieste ---
@app.post("/richieste/", response_model=schemas.Richiesta, tags=["Richieste"], status_code=status.HTTP_201_CREATED)
def crea_richiesta(richiesta: schemas.RichiestaCreate, db: Session = Depends(get_db)):
    return crud.create_richiesta(db=db, richiesta=richiesta)

@app.get("/richieste/{richiesta_id}", response_model=schemas.Richiesta, tags=["Richieste"])
def leggi_richiesta(richiesta_id: int, db: Session = Depends(get_db)):
    db_richiesta = crud.get_richiesta(db=db, richiesta_id=richiesta_id)
    if db_richiesta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Richiesta non trovata")
    return db_richiesta

@app.get("/richieste/", response_model=List[schemas.Richiesta], tags=["Richieste"])
def leggi_richieste(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    richieste = crud.get_richieste(db=db, skip=skip, limit=limit) 
    return richieste

# --- Endpoint per Articoli ---
@app.post("/articoli/", response_model=schemas.Articolo, tags=["Articoli"], status_code=status.HTTP_201_CREATED)
def crea_articolo(articolo: schemas.ArticoloCreate, db: Session = Depends(get_db)):
    return crud.create_articolo(db=db, articolo=articolo)

@app.get("/articoli/{articolo_id}", response_model=schemas.Articolo, tags=["Articoli"])
def leggi_articolo(articolo_id: int, db: Session = Depends(get_db)):
    db_articolo = crud.get_articolo(db=db, articolo_id=articolo_id) 
    if db_articolo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Articolo non trovato")
    return db_articolo

@app.get("/articoli/", response_model=List[schemas.Articolo], tags=["Articoli"])
def leggi_articoli(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    articoli = crud.get_articoli(db=db, skip=skip, limit=limit) 
    return articoli

# --- Endpoint per Immagini ---
@app.post("/immagini/", response_model=schemas.Immagine, tags=["Immagini"], status_code=status.HTTP_201_CREATED)
def crea_immagine(immagine: schemas.ImmagineCreate, db: Session = Depends(get_db)):
    return crud.create_immagine(db=db, immagine=immagine)

@app.get("/immagini/{immagine_id}", response_model=schemas.Immagine, tags=["Immagini"])
def leggi_immagine(immagine_id: int, db: Session = Depends(get_db)):
    db_immagine = crud.get_immagine(db=db, immagine_id=immagine_id) 
    if db_immagine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Immagine non trovata")
    return db_immagine

@app.get("/immagini/", response_model=List[schemas.Immagine], tags=["Immagini"])
def leggi_immagini(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    immagini = crud.get_immagini(db=db, skip=skip, limit=limit)
    return immagini