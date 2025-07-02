# Usa un'immagine base Python leggera e stabile
FROM python:3.9-slim-buster

# Imposta la directory di lavoro all'interno del container
WORKDIR /app

# Copia il file requirements.txt nel container
# Questo passo è separato per sfruttare la cache di Docker:
# se requirements.txt non cambia, Docker non reinstallerà le dipendenze.
COPY requirements.txt .

# Installa le dipendenze Python
# --no-cache-dir: non memorizza i pacchetti scaricati, riduce la dimensione dell'immagine.
# --upgrade pip: aggiorna pip per evitare warning.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia il resto del codice del tuo progetto nel container
COPY . .

# Comando di default per l'esecuzione del tuo script (non verrà usato direttamente da Cloud Build, ma è buona pratica)
CMD ["python3", "run_automation.py"]