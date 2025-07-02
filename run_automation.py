import requests
import json
import time
import os
from pathlib import Path
import re 
from datetime import datetime
import hashlib
import sys # Importa sys per accedere agli argomenti della riga di comando

from google.cloud import storage # Import della libreria Cloud Storage

# Rimuovi l'import di mail_reader se non è più usato (dovrebbe essere rimosso)
# from mail_reader import fetch_unread_emails

from email_parser import estrai_info_email
from ai_content import genera_keywords_da_contesto, genera_n_articoli
from pexels_api import cerca_e_scarica_immagine_pexels
from ai_image import genera_immagine 
from generate_site import crea_pagina_articolo, crea_home_page 
from jinja2 import Environment, FileSystemLoader

# --- Configuration ---
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000") # Potrebbe diventare un servizio cloud in futuro (es. IP di una Cloud Run)
N_ARTICOLI_TOTALI = 20

default_palette = {"background": "#f8f9fa", "text": "#343a40"} 

env = Environment(loader=FileSystemLoader('.')) 

def datetimeformat_filter(value, format='%Y'):
    if isinstance(value, str) and value == "now()":
        return datetime.now().strftime(format)
    if isinstance(value, datetime):
        return value.strftime(format)
    return value

env.filters['datetimeformat'] = datetimeformat_filter


def download_placeholder_image(placeholder_path: Path, width: int, height: int, text: str, bg_color: str, text_color: str) -> bool:
    """Scarica un'immagine placeholder se non esiste."""
    if placeholder_path.exists():
        print(f"Placeholder '{placeholder_path.name}' esiste già. Non scarico.")
        return True
    
    print(f"Creazione/download placeholder: {placeholder_path}")
    try:
        url = f"https://placehold.co/{width}x{height}/{bg_color}/{text_color}?text={text.replace(' ', '+')}"
        placeholder_img_data = requests.get(url, stream=True)
        placeholder_img_data.raise_for_status()
        placeholder_path.parent.mkdir(parents=True, exist_ok=True) 
        with open(placeholder_path, 'wb') as f:
            for chunk in placeholder_img_data.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Placeholder '{placeholder_path.name}' scaricato con successo.")
        return True
    except Exception as e:
        print(f"ERRORE durante il download del placeholder '{placeholder_path.name}': {e}")
        return False


# Modificata la funzione processa_dati_email_e_salva_sito per accettare un dict dati_email
def processa_dati_email_e_salva_sito(dati_email_str: str, input_email_filename: str = "input_generico.json"):
    """
    Processa i dati di una singola email (forniti come stringa JSON), crea/aggiorna l'azienda via API,
    e genera contenuti associati, salvandoli anch'essi via API, e infine il sito HTML.
    """
    try:
        email_data = json.loads(dati_email_str)
    except json.JSONDecodeError as e:
        print(f"ERRORE: Impossibile parsare i dati email da JSON: {e}. Contenuto: {dati_email_str[:200]}...")
        return None

    print(f"\n--- Inizio elaborazione per input: {input_email_filename} (oggetto: {email_data.get('subject', 'N/D')}) ---")
    dati_estratti = estrai_info_email(email_data['body'])
    print(f"Dati estratti dall'input: {json.dumps(dati_estratti, indent=2, ensure_ascii=False)}")

    # --- 1. Mappatura e Creazione/Recupero Azienda via API ---
    nome_azienda_api = dati_estratti.get('chi')
    if not nome_azienda_api:
        print(f"ERRORE: Nome azienda ('chi') non trovato nei dati estratti. Salto questo input.")
        return None

    email_azienda_api = dati_estratti.get('email azienda')

    if not email_azienda_api:
        timestamp_str = str(int(time.time()))[-6:]
        placeholder_email = f"contatto_fallback_{nome_azienda_api.lower().replace(' ', '_').replace('.', '')}_{timestamp_str}@esempio-test.com"
        print(f"ATTENZIONE: 'email azienda' non trovata nei dati estratti. Uso un placeholder unico: {placeholder_email}")
        email_azienda_api = placeholder_email
    else:
        print(f"Email azienda trovata ed estratta: {email_azienda_api}")

    # Build detailed description for the 'description' field in the DB
    descrizione_api_parts = []
    if dati_estratti.get('cosa'):
        descrizione_api_parts.append(f"Si occupa di: {dati_estratti['cosa']}.")
    if dati_estratti.get('come'):
        descrizione_api_parts.append(f"Opera tramite: {dati_estratti['come']}.")
    if dati_estratti.get('punti di forza'): 
        descrizione_api_parts.append(f"Punti di forza principali: {dati_estratti['punti di forza']}.")
    if dati_estratti.get('prodotti servizi'):
        descrizione_api_parts.append(f"Offre prodotti e servizi quali: {dati_estratti['prodotti servizi']}.")
    if dati_estratti.get('obbiettivi futuri'):
        descrizione_api_parts.append(f"Obiettivi futuri: {dati_estratti['obbiettivi futuri']}.")
    if dati_estratti.get('tipologia di mercato'):
        descrizione_api_parts.append(f"Opera nel mercato: {dati_estratti['tipologia di mercato']}.")

    descrizione_api = " ".join(descrizione_api_parts) if descrizione_api_parts else "Nessuna descrizione dettagliata fornita."

    # Payload for company creation/update, includes new social URLs
    payload_azienda = {
        "nome": nome_azienda_api,
        "email": email_azienda_api,
        "descrizione": descrizione_api.strip(),
        "instagram_url": dati_estratti.get('pagina social instagram', None), 
        "facebook_url": dati_estratti.get('pagina social facebook', None),   
        "google_mybusiness_url": dati_estratti.get('google mybusiness', None) 
    }

    azienda_id_db = None
    azienda_obj_db = None
    response_azienda = None

    try:
        print(f"Invio richiesta POST a {API_BASE_URL}/aziende/ con payload: {json.dumps(payload_azienda, indent=2, ensure_ascii=False)}")
        response_azienda = requests.post(f"{API_BASE_URL}/aziende/", json=payload_azienda)
        
        print(f"Risposta API Creazione Azienda - Status: {response_azienda.status_code}")

        if response_azienda.status_code == 409:
            print(f"AVVISO: Impossibile creare l'azienda '{nome_azienda_api}'. L'email '{email_azienda_api}' esiste già.")
            print("Cerco di recuperare l'ID dell'azienda esistente.")
            resp_get_aziende = requests.get(f"{API_BASE_URL}/aziende/")
            resp_get_aziende.raise_for_status()
            aziende_esistenti = resp_get_aziende.json()
            for az in aziende_esistenti:
                if az.get('email') == email_azienda_api:
                    azienda_obj_db = az
                    azienda_id_db = az['id']
                    print(f"Azienda '{az['nome']}' recuperata con ID: {azienda_id_db}.")
                    break
            if not azienda_id_db:
                print("ERRORE: Azienda esistente non trovata nonostante il conflitto. Salto questo input.")
                return None
        else:
            response_azienda.raise_for_status()
            azienda_obj_db = response_azienda.json()
            azienda_id_db = azienda_obj_db.get('id')
            
            if azienda_id_db:
                print(f"SUCCESSO: Azienda '{azienda_obj_db.get('nome')}' creata con ID: {azienda_id_db} nel database.")
            else:
                print(f"ERRORE: L'API non ha restituito un ID per l'azienda. Risposta: {json.dumps(azienda_obj_db, indent=2, ensure_ascii=False)}")
                return None

    except requests.exceptions.HTTPError as http_err:
        print(f"ERRORE HTTP durante la creazione/recupero dell'azienda: {http_err}")
        if response_azienda is not None:
            print(f"Dettaglio errore API: {response_azienda.text}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"ERRORE DI RICHIESTA (es. server API non raggiungibile) durante creazione/recupero azienda: {req_err}")
        return None
    except Exception as e:
        print(f"GENERIC ERROR durante il processo API per l'azienda {nome_azienda_api}: {e}")
        return None

    if not azienda_id_db:
        print("Elaborazione fallita: non è stato possibile creare o identificare l'azienda nel DB.")
        return None

    # --- Prepara la cartella per i siti e le immagini dell'azienda ---
    print(f"\n--- Inizio generazione contenuti per Azienda ID: {azienda_id_db} ({nome_azienda_api}) ---")
    
    # Crea un nome di directory sicuro e conciso per la cartella dell'azienda
    nome_cartella_pulito = re.sub(r'[^\w\s-]', '', nome_azienda_api).replace(' ', '-').lower()
    hash_nome = hashlib.md5(nome_cartella_pulito.encode('utf-8')).hexdigest()[:6]
    cartella_azienda = f"{nome_cartella_pulito}-{hash_nome}" 

    public_dir = Path("public") / cartella_azienda
    public_dir.mkdir(parents=True, exist_ok=True)
    
    images_dir = public_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    print(f"Cartella per i siti creata/assicurata: {public_dir}")
    print(f"Immagini cartella creata/assicurata: {images_dir}")

    # --- 2. Generazione delle 20 Keyword ---
    print(f"Sto per generare {N_ARTICOLI_TOTALI} keyword dall'input...")
    keywords_generate = genera_keywords_da_contesto(dati_estratti, n_keywords=N_ARTICOLI_TOTALI)
    
    if not keywords_generate:
        print("Nessuna keyword generata. Impossibile procedere con gli articoli.")
        return None

    print(f"Keyword generate: {keywords_generate}")

    # --- 3. Generazione e Salvataggio Immagine Principale (per la home page) ---
    print(f"\nSto per generare/cercare l'immagine principale per la home page (prima DALL-E, poi Pexels)...")
    
    concise_home_query = dati_estratti.get('cosa')
    if concise_home_query and len(concise_home_query.split()) > 5: 
        concise_home_query = " ".join(concise_home_query.split()[:3]) 
    elif not concise_home_query: 
        concise_home_query = nome_azienda_api

    query_immagine_home_ai = f"professional cover image for a company of {dati_estratti.get('cosa', nome_azienda_api)}. digital art, modern, clean style." 
    query_immagine_home_pexel = f"{concise_home_query} business technology" 
    query_immagine_home_pexel = re.sub(r'\s+', ' ', query_immagine_home_pexel).strip()


    url_immagine_home_final = "" 
    
    placeholder_home_path = Path("public") / "placeholder_home_image.jpeg"
    download_placeholder_image(placeholder_home_path, 800, 600, "Home Page Image", "CCCCCC", "4F4F4F")
    url_immagine_home_final = os.path.relpath(placeholder_home_path, public_dir).replace('\\', '/')
    print(f"Percorso placeholder homepage di default: {url_immagine_home_final}")

    local_image_path_obj_home = None
    
    # Try DALL-E first
    print(f"IMMAGINE HOME PAGE: Tentativo con DALL-E per la home: '{query_immagine_home_ai}'")
    try:
        dalle_image_url_home = genera_immagine(query_immagine_home_ai) 
        if dalle_image_url_home:
            image_name_dalle_home = f"home_image_dalle_{hashlib.md5(query_immagine_home_ai.encode('utf-8')).hexdigest()[:8]}.png"
            local_image_path_obj_home = images_dir / image_name_dalle_home
            print(f"IMMAGINE HOME PAGE: Scaricando immagine DALL-E per home da: {dalle_image_url_home}")
            img_data_dalle_home = requests.get(dalle_image_url_home, stream=True)
            img_data_dalle_home.raise_for_status()
            with open(local_image_path_obj_home, 'wb') as f:
                for chunk in img_data_dalle_home.iter_content(chunk_size=8192):
                    f.write(chunk)
            url_immagine_home_final = f"images/{local_image_path_obj_home.name}"
            print(f"IMMAGINE HOME PAGE: DALL-E salvata localmente: {url_immagine_home_final}")
        else:
            print("IMMAGINE HOME PAGE: DALL-E non ha generato un'immagine valida per la home.")
    except Exception as e:
        print(f"IMMAGINE HOME PAGE: Errore durante la generazione/download immagine DALL-E per home: {e}.")

    # If DALL-E failed, try Pexels
    if not local_image_path_obj_home:
        print(f"IMMAGINE HOME PAGE: DALL-E fallito, tentativo con Pexels per: '{query_immagine_home_pexel}'")
        try:
            query_hash_home = hashlib.md5(query_immagine_home_pexel.encode('utf-8')).hexdigest()[:8] # Correzione qui
            local_image_path_obj_home = cerca_e_scarica_immagine_pexels(
                query=query_immagine_home_pexel, 
                save_path=images_dir, 
                filename_prefix=f"home_image_pex_{query_hash_home}", 
                orientation="landscape" 
            )
            if local_image_path_obj_home:
                url_immagine_home_final = f"images/{Path(local_image_path_obj_home).name}" 
                print(f"IMMAGINE HOME PAGE: Pexels trovata e salvata: {url_immagine_home_final}")
            else:
                print(f"IMMAGINE HOME PAGE: Ricerca Pexels fallita per immagine principale. Uso placeholder.")
        except Exception as e:
            print(f"IMMAGINE HOME PAGE: Errore generico durante la ricerca Pexels: {e}. Uso placeholder.")
    
    # If no image was found, use the default placeholder path already set
    if not url_immagine_home_final or url_immagine_home_final == os.path.relpath(placeholder_home_path, public_dir).replace('\\', '/'):
        print("IMMAGINE HOME PAGE: Nessuna immagine trovata/generata. Utilizzo il placeholder predefinito.")
        url_immagine_home_final = os.path.relpath(placeholder_home_path, public_dir).replace('\\', '/')

    print(f"IMMAGINE HOME PAGE: Percorso finale usato nel template: {url_immagine_home_final}")

    # Salva l'URL dell'immagine principale nel DB (indipendentemente dalla fonte)
    payload_immagine_home_db = {
        "url": url_immagine_home_final, 
        "descrizione": f"Main image for {nome_azienda_api}",
        "azienda_id": azienda_id_db
    }
    try:
        response_img_home = requests.post(f"{API_BASE_URL}/immagini/", json=payload_immagine_home_db)
        response_img_home.raise_for_status()
        print(f"Homepage image for '{nome_azienda_api}' saved in DB with ID: {response_img_home.json().get('id')}.")
    except Exception as e:
        print(f"ERRORE salvataggio immagine home nel DB: {e}")


    # --- 4. Generate and Save Articles via API (one for each keyword with unique image) ---
    print(f"Sto per generare {N_ARTICOLI_TOTALI} articoli con immagini individuali...")
    articoli_per_html = [] 
    
    placeholder_article_path = Path("public") / "placeholder_article_image.jpeg"
    download_placeholder_image(placeholder_article_path, 400, 300, "Articolo Immagine", "DDDDDD", "6F6F6F")
    relative_placeholder_article_url = os.path.relpath(placeholder_article_path, public_dir).replace('\\', '/')
    print(f"Percorso placeholder articolo di default: {relative_placeholder_article_url}")

    placeholder_sidebar_path = Path("public") / "placeholder_sidebar_image.jpeg"
    download_placeholder_image(placeholder_sidebar_path, 300, 450, "Sidebar Image", "AAAAAA", "333333") 
    relative_placeholder_sidebar_url = os.path.relpath(placeholder_sidebar_path, public_dir).replace('\\', '/')
    print(f"Percorso placeholder sidebar articolo di default: {relative_placeholder_sidebar_url}")


    try:
        articoli_da_ai_raw = genera_n_articoli(dati_estratti, keywords_generate, n_max=N_ARTICOLI_TOTALI)
        
        if not articoli_da_ai_raw:
            print("No articles generated by AI.")
            return None

        for i, art_data_from_ai in enumerate(articoli_da_ai_raw):
            if i > 0: 
                print(f"PAUSA: Attendo 25 secondi prima di generare il prossimo articolo/immagini per evitare il rate limit di OpenAI.")
                time.sleep(25) 

            print(f"ARTICOLO {i+1}: Gestione immagine per articolo '{art_data_from_ai.get('titolo', art_data_from_ai['keywords'])}'")
            
            tema_specifico_articolo = art_data_from_ai['keywords']
            query_immagine_pexel = tema_specifico_articolo 
            query_immagine_pexel = re.sub(r'\s+', ' ', query_immagine_pexel).strip() 

            url_immagine_articolo_html_final = relative_placeholder_article_url 
            url_immagine_sidebar_final = relative_placeholder_sidebar_url 


            local_image_path_obj_article = None
            local_image_path_obj_sidebar = None 

            # --- Gestione Immagine Principale Articolo (Priorità DALL-E) ---
            dalle_prompt_main_article = f"Un'immagine principale rappresentativa e professionale per un articolo su '{tema_specifico_articolo}'. Stile digitale, moderno, pulito."
            print(f"ARTICOLO {i+1}: Tentativo DALL-E per immagine principale: '{dalle_prompt_main_article}'")
            try:
                dalle_image_url_main_article = genera_immagine(dalle_prompt_main_article) 
                if dalle_image_url_main_article:
                    image_name_dalle_main_article = f"article_dalle_{i+1}_main_{hashlib.md5(dalle_prompt_main_article.encode('utf-8')).hexdigest()[:8]}.png"
                    local_image_path_obj_article = images_dir / image_name_dalle_main_article
                    print(f"ARTICOLO {i+1}: Scaricando immagine DALL-E (main) da: {dalle_image_url_main_article}")
                    requests.get(dalle_image_url_main_article, stream=True).raise_for_status()
                    with open(local_image_path_obj_article, 'wb') as f:
                        for chunk in requests.get(dalle_image_url_main_article, stream=True).iter_content(chunk_size=8192):
                            f.write(chunk)
                    url_immagine_articolo_html_final = f"images/{local_image_path_obj_article.name}"
                    print(f"ARTICOLO {i+1}: Immagine principale DALL-E salvata localmente: {url_immagine_articolo_html_final}")
                else:
                    print("ARTICOLO {i+1}: DALL-E non ha generato un'immagine principale valida.")
            except Exception as e:
                print(f"ARTICOLO {i+1}: Errore DALL-E (main): {e}.")
            
            # If DALL-E failed for main image, try Pexels
            if not local_image_path_obj_article:
                print(f"ARTICOLO {i+1}: DALL-E fallito per immagine principale, tentativo Pexels per: '{query_immagine_pexel}'")
                try:
                    query_hash_article = hashlib.md5(query_immagine_pexel.encode('utf-8')).hexdigest()[:8] # Correzione qui
                    local_image_path_obj_article = cerca_e_scarica_immagine_pexels(
                        query=query_immagine_pexel, 
                        save_path=images_dir,
                        filename_prefix=f"article_{i+1}_main_pex_{query_hash_article}", 
                        orientation="landscape" 
                    )
                    if local_image_path_obj_article:
                        url_immagine_articolo_html_final = f"images/{Path(local_image_path_obj_article).name}"
                        print(f"ARTICOLO {i+1}: Immagine principale Pexels trovata e salvata: {url_immagine_articolo_html_final}")
                    else:
                        print(f"ARTICOLO {i+1}: Ricerca Pexels fallita per immagine principale. Uso placeholder.")
                except Exception as e:
                    print(f"ARTICOLO {i+1}: Errore Pexels (main): {e}. Uso placeholder.")

            # --- Gestione Immagine Sidebar Articolo (Priorità DALL-E) ---
            dalle_prompt_sidebar_article = f"Un'immagine verticale e professionale che illustri un dettaglio o un concetto secondario legato a '{tema_specifico_articolo}'. Stile digitale, moderno, pulito."
            print(f"ARTICOLO {i+1}: Tentativo DALL-E per immagine sidebar: '{dalle_prompt_sidebar_article}'")
            try:
                dalle_image_url_sidebar_article = genera_immagine(dalle_prompt_sidebar_article)
                if dalle_image_url_sidebar_article:
                    image_name_dalle_sidebar_article = f"article_dalle_{i+1}_sidebar_{hashlib.md5(dalle_prompt_sidebar_article.encode('utf-8')).hexdigest()[:8]}.png"
                    local_image_path_obj_sidebar = images_dir / image_name_dalle_sidebar_article
                    print(f"ARTICOLO {i+1}: Scaricando immagine DALL-E (sidebar) da: {dalle_image_url_sidebar_article}")
                    requests.get(dalle_image_url_sidebar_article, stream=True).raise_for_status()
                    with open(local_image_path_obj_sidebar, 'wb') as f:
                        for chunk in requests.get(dalle_image_url_sidebar_article, stream=True).iter_content(chunk_size=8192):
                            f.write(chunk)
                    url_immagine_sidebar_final = f"images/{local_image_path_obj_sidebar.name}"
                    print(f"ARTICOLO {i+1}: Immagine sidebar DALL-E salvata localmente: {url_immagine_sidebar_final}")
                else:
                    print("ARTICOLO {i+1}: DALL-E non ha generato un'immagine sidebar valida.")
            except Exception as e:
                print(f"ARTICOLO {i+1}: Errore DALL-E (sidebar): {e}.")

            # If DALL-E failed for sidebar image, try Pexels
            if not local_image_path_obj_sidebar:
                print(f"ARTICOLO {i+1}: DALL-E fallito per immagine sidebar, tentativo Pexels per: '{tema_specifico_articolo} detail'")
                try:
                    query_hash_sidebar = hashlib.md5(f"{tema_specifico_articolo} detail".encode('utf-8')).hexdigest()[:8] # Correzione qui
                    local_image_path_obj_sidebar = cerca_e_scarica_immagine_pexels(
                        query=f"{tema_specifico_articolo} detail", 
                        save_path=images_dir,
                        filename_prefix=f"article_{i+1}_sidebar_pex_{query_hash_sidebar}", 
                        orientation="portrait" 
                    )
                    if local_image_path_obj_sidebar:
                        url_immagine_sidebar_final = f"images/{Path(local_image_path_obj_sidebar).name}"
                        print(f"ARTICOLO {i+1}: Immagine sidebar Pexels trovata e salvata: {url_immagine_sidebar_final}")
                    else:
                        print(f"ARTICOLO {i+1}: Ricerca Pexels fallita per immagine sidebar. Uso placeholder.")
                except Exception as e:
                    print(f"ARTICOLO {i+1}: Errore Pexels (sidebar): {e}. Uso placeholder.")


            print(f"ARTICOLO {i+1}: Percorso finale immagine principale: {url_immagine_articolo_html_final}")
            print(f"ARTICOLO {i+1}: Percorso finale immagine sidebar: {url_immagine_sidebar_final}")


            payload_articolo = {
                "titolo": art_data_from_ai["titolo"],
                "contenuto": art_data_from_ai["contenuto"],
                "keywords": art_data_from_ai["keywords"],
                "url_immagine": url_immagine_articolo_html_final,
                "url_immagine_sidebar": url_immagine_sidebar_final, 
                "azienda_id": azienda_id_db
            }
            print(f"Invio richiesta POST a {API_BASE_URL}/articoli/ for l'articolo {i+1} ('{payload_articolo['titolo']}')")
            response_articolo = requests.post(f"{API_BASE_URL}/articoli/", json=payload_articolo)
            response_articolo.raise_for_status()
            articolo_salvato_db = response_articolo.json()
            print(f"Article '{articolo_salvato_db.get('titolo')}' saved in DB with ID: {articolo_salvato_db.get('id')}.")
            
            articolo_salvato_db['sottotitolo'] = art_data_from_ai.get('sottotitolo', '') 
            articolo_salvato_db['img_url_preview'] = url_immagine_articolo_html_final
            articolo_salvato_db['sidebar_img_url'] = url_immagine_sidebar_final 
            articoli_per_html.append(articolo_salvato_db) 

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP ERROR during article creation/saving: {http_err}")
        if 'response_articolo' in locals() and response_articolo is not None:
            print(f"API error detail: {response_articolo.text}")
        return None
    except Exception as e:
        print(f"GENERIC ERROR during article generation/saving: {e}")
        return None

    # --- 5. Create HTML Pages (Homepage and Article Pages) ---
    print(f"\nSto per generare la home page e le pagine degli articoli HTML...")
    
    # Footer data (extract or use fallback)
    footer_data = {
        "nome_azienda": dati_estratti.get('chi', 'Our Company'),
        "partita_iva": dati_estratti.get('partita iva', 'Not specified'),
        "indirizzo": dati_estratti.get('dove', 'Address not specified'),
        "telefono": dati_estratti.get('numero di telefono', 'Not specified'), 
        "email_azienda": dati_estratti.get('email azienda', 'info@example.com'),
        "cookie_policy_url": dati_estratti.get('cookie policy url', '#')
    }
    # Pass social URLs from extracted data to footer_data as well for article template
    # This ensures footer in article template has correct social links.
    footer_data['instagram_url'] = dati_estratti.get('pagina social instagram', None)
    footer_data['facebook_url'] = dati_estratti.get('pagina social facebook', None)
    footer_data['google_mybusiness_url'] = dati_estratti.get('google mybusiness', None)


    # --- Generate Single Article Pages ---
    for i, articolo in enumerate(articoli_per_html):
        titolo_pulito = re.sub(r'[^\w\s-]', '', articolo['titolo']).replace(' ', '-').lower()
        nome_file_articolo = public_dir / f"articolo_{i+1}_{titolo_pulito}.html"
        
        html_articolo_output = crea_pagina_articolo(
            jinja_env=env, 
            titolo=articolo['titolo'],
            sottotitolo=articolo['sottotitolo'],
            keywords=articolo['keywords'],
            img_url=articolo['url_immagine'], 
            sidebar_img_url=articolo['sidebar_img_url'], 
            contenuto=articolo['contenuto'],
            palette=default_palette,
            footer_data=footer_data
        )
        try:
            with open(nome_file_articolo, "w", encoding="utf-8") as f:
                f.write(html_articolo_output)
            print(f"SUCCESS: Article '{articolo['titolo']}' saved to: {nome_file_articolo}")
            
            articoli_per_html[i]['url'] = f"{nome_file_articolo.name}"
            articoli_per_html[i]['img_url_preview'] = articolo['url_immagine'] 
        except Exception as e:
            print(f"ERROR saving article HTML file '{nome_file_articolo}': {e}")


    # --- Generate Homepage (Index) ---
    home_page_title = f"{dati_estratti.get('chi', 'Our Company')}" 
    home_page_subtitle = f"Explore our articles on {dati_estratti.get('cosa', 'our services')}"
    
    # This is the main content that will go into the home-content div
    home_page_main_content = f"""
    <p>Benvenuti sul sito di <strong>{dati_estratti.get('chi', 'la nostra azienda')}</strong>, 
    specializzata in <strong>{dati_estratti.get('cosa', 'soluzioni innovative')}</strong>. 
    Siamo qui per fornirti informazioni approfondite sul nostro settore e sui nostri servizi. 
    Scopri come i nostri punti di forza, come <em>{dati_estratti.get('punti di forza', 'innovazione e qualità')}</em>, 
    possono aiutare i nostri clienti.</p>
    <p>Di seguito trovi una selezione dei nostri articoli più recenti, pensati per offrirti spunti e conoscenze utili.</p>
    """

    # Dictionary with social URLs for the homepage
    social_urls = {
        "instagram": dati_estratti.get('pagina social instagram', None),
        "facebook": dati_estratti.get('pagina social facebook', None),
        "google_mybusiness": dati_estratti.get('google mybusiness', None)
    }

    html_output_main_index = crea_home_page(
        jinja_env=env, 
        titolo=home_page_title,
        sottotitolo=home_page_subtitle,
        keywords=",".join(keywords_generate), 
        img_url_home=url_immagine_home_final, 
        home_content=home_page_main_content,
        articoli=articoli_per_html,
        palette=default_palette,
        footer_data=footer_data,
        social_urls=social_urls 
    )

    nome_file_home_index = public_dir / "index.html"
    try:
        with open(nome_file_home_index, "w", encoding="utf-8") as f:
            f.write(html_output_main_index)
        print(f"SUCCESS: Homepage indexed for {nome_azienda_api} generated and saved in: {nome_file_home_index}")
    except Exception as e:
        print(f"ERROR saving homepage HTML file '{nome_file_home_index}': {e}") 
    
    print(f"--- Processing for {nome_azienda_api} completed ---")
    return azienda_obj_db


def avvia_processo_completo():
    print("Starting full automation process...")
    # Cloud Build passerà il percorso del file JSON come argomento
    if len(sys.argv) > 1:
        input_json_file = sys.argv[1]
        print(f"Lettura input da file JSON: {input_json_file}")
        try:
            with open(input_json_file, 'r', encoding='utf-8') as f:
                email_data_content = f.read()
            # Chiama la nuova funzione di elaborazione
            processa_dati_email_e_salva_sito(email_data_content, input_email_filename=Path(input_json_file).name)
        except FileNotFoundError:
            print(f"ERRORE: File di input JSON non trovato: {input_json_file}")
        except Exception as e:
            print(f"ERRORE durante la lettura o elaborazione del file JSON: {e}")
    else:
        print("ATTENZIONE: Nessun file JSON di input specificato. Esegui in modalità locale (non automatica).")
        # Logica per l'esecuzione locale se non viene passato un argomento (opzionale)
        # Qui potresti rimettere la logica di fetch_unread_emails() o un input manuale per test
        # Per ora, semplicemente non fa nulla se non c'è input.
        print("Esegui manualmente: python run_automation.py <percorso_al_file_json_locale_di_test>")

    print("\nFull automation process completed.")

if __name__ == "__main__":
    avvia_processo_completo()