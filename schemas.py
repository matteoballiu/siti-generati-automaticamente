# schemas.py
from pydantic import BaseModel, EmailStr # EmailStr per validazione email
from typing import List, Optional
from datetime import datetime # Per i campi timestamp nelle risposte

# --- Schemi di Base (per input e output comuni) e Schemi di Creazione ---

class ArticoloBase(BaseModel):
    titolo: str
    contenuto: str
    keywords: Optional[str] = None
    url_immagine: Optional[str] = None # Immagine principale dell'articolo
    url_immagine_sidebar: Optional[str] = None # NUOVO CAMPO: Immagine per la sidebar/layout a 2 colonne

class ArticoloCreate(ArticoloBase):
    azienda_id: int # L'ID dell'azienda a cui l'articolo è associato

class ImmagineBase(BaseModel):
    url: str
    descrizione: Optional[str] = None

class ImmagineCreate(ImmagineBase):
    azienda_id: int # L'ID dell'azienda a cui l'immagine è associata

class RichiestaBase(BaseModel):
    titolo: str
    descrizione: str

class RichiestaCreate(RichiestaBase):
    utente_id: int # L'ID dell'utente che ha fatto la richiesta

class UtenteBase(BaseModel):
    nome: str
    email: EmailStr # Usa EmailStr per la validazione automatica dell'email

class UtenteCreate(UtenteBase):
    password: str # La password verrà ricevuta in chiaro, l'hashing avverrà nel backend
    azienda_id: int # L'ID dell'azienda a cui l'utente è associato

class AziendaBase(BaseModel):
    nome: str
    email: EmailStr
    descrizione: Optional[str] = None
    instagram_url: Optional[str] = None      # NUOVO
    facebook_url: Optional[str] = None       # NUOVO
    google_mybusiness_url: Optional[str] = None # NUOVO

class AziendaCreate(AziendaBase):
    pass # Al momento non ha campi aggiuntivi rispetto ad AziendaBase per la creazione

class Azienda(AziendaBase): 
    id: int
    data_creazione: datetime
    data_ultima_modifica: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- Schemi per le Risposte API (includono ID e timestamp) ---

# Re-defines Articolo and Immagine based on their Base schemas + ID/timestamps
# Ensure all fields are explicitly listed or inherited correctly

class Articolo(ArticoloBase): 
    id: int
    azienda_id: int 
    data_creazione: datetime
    data_ultima_modifica: Optional[datetime] = None 

    class Config:
        from_attributes = True 

class Immagine(ImmagineBase): 
    id: int
    azienda_id: int
    data_creazione: datetime
    data_ultima_modifica: Optional[datetime] = None

    class Config:
        from_attributes = True

class Richiesta(RichiestaBase): 
    id: int
    utente_id: int
    data_creazione: datetime
    data_ultima_modifica: Optional[datetime] = None

    class Config:
        from_attributes = True

class Utente(UtenteBase): # Schema per la risposta API (SENZA password)
    id: int
    azienda_id: int
    data_creazione: datetime
    data_ultima_modifica: Optional[datetime] = None
    # NON includere la password nella risposta API per motivi di sicurezza

    class Config:
        from_attributes = True