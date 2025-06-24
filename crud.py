# crud.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import List, Optional 

import models # Il tuo models.py
import schemas # Il tuo schemas.py


# --- Funzioni CRUD per Azienda ---
def create_azienda(db: Session, azienda: schemas.AziendaCreate) -> models.Azienda:
    # `model_dump()` include tutti i campi definiti in schemas.AziendaCreate, inclusi i nuovi URL
    db_azienda = models.Azienda(**azienda.model_dump())
    db.add(db_azienda)
    try:
        db.commit()
        db.refresh(db_azienda)
    except IntegrityError:
        db.rollback() 
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail=f"Un'azienda con email '{azienda.email}' esiste già."
        )
    return db_azienda

def get_azienda(db: Session, azienda_id: int) -> Optional[models.Azienda]:
    return db.query(models.Azienda).filter(models.Azienda.id == azienda_id).first()

def get_aziende(db: Session, skip: int = 0, limit: int = 100) -> List[models.Azienda]:
    return db.query(models.Azienda).offset(skip).limit(limit).all()

# --- Funzioni CRUD per Utente ---
def create_utente(db: Session, utente: schemas.UtenteCreate) -> models.Utente:
    # IMPORTANTE: Implementare l'hashing della password qui prima di creare l'oggetto Utente!
    # Questo è un placeholder e NON è sicuro per la produzione.
    # Esempio con passlib:
    # from passlib.context import CryptContext
    # pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    # hashed_password = pwd_context.hash(utente.password)
    # db_utente_data = utente.model_dump(exclude={"password"}) 
    # db_utente = models.Utente(**db_utente_data, password=hashed_password)
    
    # Per ora, usiamo la password come fornita, ma con .model_dump()
    # ATTENZIONE: SALVARE PASSWORD IN CHIARO È UN RISCHIO DI SICUREZZA.
    db_utente = models.Utente(**utente.model_dump())
    db.add(db_utente)
    try:
        db.commit()
        db.refresh(db_utente)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail=f"Un utente con email '{utente.email}' esiste già."
        )
    return db_utente

def get_utente(db: Session, utente_id: int) -> Optional[models.Utente]:
    return db.query(models.Utente).filter(models.Utente.id == utente_id).first()

def get_utenti(db: Session, skip: int = 0, limit: int = 100) -> List[models.Utente]:
    return db.query(models.Utente).offset(skip).limit(limit).all()

# --- Funzioni CRUD per Richiesta ---
def create_richiesta(db: Session, richiesta: schemas.RichiestaCreate) -> models.Richiesta:
    db_richiesta = models.Richiesta(**richiesta.model_dump())
    db.add(db_richiesta)
    db.commit()
    db.refresh(db_richiesta)
    return db_richiesta

def get_richiesta(db: Session, richiesta_id: int) -> Optional[models.Richiesta]:
    return db.query(models.Richiesta).filter(models.Richiesta.id == richiesta_id).first()

def get_richieste(db: Session, skip: int = 0, limit: int = 100) -> List[models.Richiesta]:
    return db.query(models.Richiesta).offset(skip).limit(limit).all()

# --- Funzioni CRUD per Articolo ---
def create_articolo(db: Session, articolo: schemas.ArticoloCreate) -> models.Articolo:
    # model_dump() ora include url_immagine_sidebar grazie alle modifiche in schemas.py
    db_articolo = models.Articolo(**articolo.model_dump()) 
    db.add(db_articolo)
    db.commit()
    db.refresh(db_articolo)
    return db_articolo

def get_articolo(db: Session, articolo_id: int) -> Optional[models.Articolo]:
    return db.query(models.Articolo).filter(models.Articolo.id == articolo_id).first()

def get_articoli(db: Session, skip: int = 0, limit: int = 100) -> List[models.Articolo]:
    return db.query(models.Articolo).offset(skip).limit(limit).all()

# --- Funzioni CRUD per Immagine ---
def create_immagine(db: Session, immagine: schemas.ImmagineCreate) -> models.Immagine:
    db_immagine = models.Immagine(**immagine.model_dump())
    db.add(db_immagine)
    db.commit()
    db.refresh(db_immagine)
    return db_immagine

def get_immagine(db: Session, immagine_id: int) -> Optional[models.Immagine]:
    return db.query(models.Immagine).filter(models.Immagine.id == immagine_id).first()

def get_immagini(db: Session, skip: int = 0, limit: int = 100) -> List[models.Immagine]:
    return db.query(models.Immagine).offset(skip).limit(limit).all()