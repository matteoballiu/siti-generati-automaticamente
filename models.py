# models.py
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func # Per i timestamp di default
from database import Base # Importa la Base da database.py

class Azienda(Base):
    __tablename__ = "aziende" 

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    descrizione = Column(Text, nullable=True)
    
    # Nuovi campi per gli URL Social/Business
    instagram_url = Column(String, nullable=True) # NUOVO
    facebook_url = Column(String, nullable=True)  # NUOVO
    google_mybusiness_url = Column(String, nullable=True) # NUOVO
    
    # Timestamp
    data_creazione = Column(DateTime(timezone=True), server_default=func.now())
    data_ultima_modifica = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()) 

    # Relazioni: un'azienda può avere molti utenti, articoli e immagini
    utenti = relationship("Utente", back_populates="azienda_rel", cascade="all, delete-orphan")
    articoli = relationship("Articolo", back_populates="azienda_rel", cascade="all, delete-orphan")
    immagini = relationship("Immagine", back_populates="azienda_rel", cascade="all, delete-orphan")


class Utente(Base):
    __tablename__ = "utenti"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    
    azienda_id = Column(Integer, ForeignKey("aziende.id"), nullable=False)
    
    data_creazione = Column(DateTime(timezone=True), server_default=func.now())
    data_ultima_modifica = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    azienda_rel = relationship("Azienda", back_populates="utenti")
    richieste = relationship("Richiesta", back_populates="utente_rel", cascade="all, delete-orphan")


class Richiesta(Base):
    __tablename__ = "richieste"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    titolo = Column(String, nullable=False)
    descrizione = Column(Text, nullable=True)
    
    utente_id = Column(Integer, ForeignKey("utenti.id"), nullable=False)
    
    data_creazione = Column(DateTime(timezone=True), server_default=func.now())
    data_ultima_modifica = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    utente_rel = relationship("Utente", back_populates="richieste")


class Articolo(Base):
    __tablename__ = "articoli"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    titolo = Column(String, nullable=False)
    contenuto = Column(Text, nullable=False)
    keywords = Column(String, nullable=True)
    url_immagine = Column(String, nullable=True) # Immagine principale dell'articolo
    url_immagine_sidebar = Column(String, nullable=True) # NUOVO CAMPO: Immagine per la sidebar/layout a 2 colonne
    
    azienda_id = Column(Integer, ForeignKey("aziende.id"), nullable=False)
    
    data_creazione = Column(DateTime(timezone=True), server_default=func.now())
    data_ultima_modifica = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    azienda_rel = relationship("Azienda", back_populates="articoli")


class Immagine(Base):
    __tablename__ = "immagini"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    url = Column(String, nullable=False)
    descrizione = Column(String, nullable=True)
    
    azienda_id = Column(Integer, ForeignKey("aziende.id"), nullable=False)

    data_creazione = Column(DateTime(timezone=True), server_default=func.now())
    data_ultima_modifica = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    azienda_rel = relationship("Azienda", back_populates="immagini")