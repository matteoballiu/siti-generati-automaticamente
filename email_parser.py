# email_parser.py (AGGIORNATO CON NUOVE CHIAVI)

import re

def estrai_info_email(email_body: str) -> dict:
    """
    Estrae informazioni strutturate dal corpo di un'email, gestendo valori su più righe.
    Si aspetta chiavi seguite da due punti (es. "chi: Nome Azienda").
    """
    chiavi = [
        "chi",
        "cosa", # Può essere molto dettagliato
        "come",
        "quando",
        "dove",
        "prodotti servizi",       # NUOVO CAMPO
        "email azienda",
        "partita iva",
        "numero di telefono",     # MODIFICATO/UNIFICATO (ex 'telefono')
        "miglioramenti",
        "tipologia di mercato",   # NUOVO CAMPO
        "punti di forza",         # Rinominato da 'forza'
        "obbiettivi futuri",      # NUOVO CAMPO
        "pagina social instagram",# NUOVO CAMPO
        "pagina social facebook", # NUOVO CAMPO
        "google mybusiness",      # NUOVO CAMPO
        "cookie policy url"       # Già presente
    ]
    
    # Crea un set di tutti i prefissi chiave in minuscolo per controlli rapidi
    chiavi_lower_prefixes = {f"{k.lower()}:" for k in chiavi}
    
    dati = {chiave: "" for chiave in chiavi} # Inizializza tutte le chiavi con stringa vuota

    if not isinstance(email_body, str):
        print("Warning: email_body non è una stringa, restituisco dati vuoti.")
        return dati

    lines = email_body.split('\n')
    current_key = None
    
    for i, line in enumerate(lines):
        stripped_line = line.strip()
        if not stripped_line: # Ignora linee vuote
            continue

        # Controlla se la riga inizia con una chiave nota
        found_new_key = False
        for chiave in chiavi:
            expected_prefix = f"{chiave.lower()}:"
            if stripped_line.lower().startswith(expected_prefix):
                if current_key: # Se c'era una chiave precedente, pulisci il suo valore
                    dati[current_key] = dati[current_key].strip()
                
                current_key = chiave # Imposta la nuova chiave
                # Estrai il valore iniziale, rimuovendo il prefisso
                valore = stripped_line[len(expected_prefix):].strip()
                dati[current_key] = valore
                found_new_key = True
                break
        
        if not found_new_key and current_key:
            # Se non abbiamo trovato una nuova chiave, e siamo già su una chiave,
            # questa riga è una continuazione del valore della chiave corrente.
            dati[current_key] += " " + stripped_line # Aggiungi la riga al valore corrente

    # Assicurati di pulire l'ultima chiave estratta (se presente)
    if current_key:
        dati[current_key] = dati[current_key].strip()
            
    return dati