import openai
import os
# from dotenv import load_dotenv # Rimosso: le credenziali saranno da variabili d'ambiente Cloud Build
import json
import re 

# load_dotenv() # Rimosso

api_key_openai = os.getenv("OPENAI_API_KEY")
if not api_key_openai:
    raise ValueError("La variabile d'ambiente OPENAI_API_KEY non è stata impostata. Assicurati che Secret Manager e Cloud Build la forniscano.")

client = openai.OpenAI(api_key=api_key_openai)

def genera_keywords_da_contesto(dati: dict, n_keywords: int = 20) -> list:
    """
    Genera un elenco di parole chiave pertinenti basandosi sui dati estratti da un'email.
    Chiede all'LLM di restituire le keyword in formato JSON.
    """
    chi = dati.get('chi', 'un\'azienda')
    cosa = dati.get('cosa', 'generico')
    descrizione_base = f"L'azienda {chi} opera nel settore di {cosa}."
    if dati.get('forza'):
        descrizione_base += f" I suoi punti di forza includono: {dati['forza']}."
    if dati.get('miglioramento'):
        descrizione_base += f" Vuole migliorare in: {dati['miglioramento']}."

    prompt = f"""
    Dato il seguente contesto aziendale:
    "{descrizione_base}"

    Genera {n_keywords} parole chiave SEO uniche e strettamente pertinenti a questo contesto.
    Le parole chiave dovrebbero essere variegate ma tutte connesse al tema principale,
    adatte per articoli di blog che esplorano diverse sfaccettature dell'attività dell'azienda.
    Restituisci le parole chiave come un array JSON di stringhe, senza altri commenti o testo.
    Esempio: ["keyword1", "keyword2", "keyword3", ..., "keyword{n_keywords}"]
    """
    
    print(f"Richiesta generazione {n_keywords} keyword a OpenAI per: {cosa}...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": "Sei un esperto SEO e di marketing. Generi parole chiave pertinenti e in formato JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"} 
        )
        
        content = response.choices[0].message.content
        print(f"Risposta raw da OpenAI per keyword: {content}")
        
        keywords = []
        try:
            parsed_content = json.loads(content)
            if isinstance(parsed_content, dict):
                if "keywords" in parsed_content:
                    keywords = parsed_content["keywords"]
                elif "data" in parsed_content and isinstance(parsed_content["data"], list):
                    keywords = parsed_content["data"]
                elif len(parsed_content) == 1 and isinstance(list(parsed_content.values())[0], list):
                    keywords = list(parsed_content.values())[0]
                else:
                    print("Warning: JSON parsato ma struttura inattesa per le keyword. Tentativo di estrazione da stringa raw.")
                    keywords = [k.strip() for k in content.replace('[', '').replace(']', '').replace('"', '').split(',') if k.strip()]
            elif isinstance(parsed_content, list):
                keywords = parsed_content
            else:
                print(f"Warning: Contenuto JSON non array o dict. Tentativo di estrazione da stringa raw.")
                keywords = [k.strip() for k in content.replace('[', '').replace(']', '').replace('"', '').split(',') if k.strip()]
            
            keywords = [k for k in keywords if isinstance(k, str) and k.strip()]
            
            if not keywords:
                print("Warning: Nessuna keyword valida estratta dopo il parsing iniziale.")
                matches = re.findall(r'"([^"]+)"', content) 
                if not matches:
                    matches = [k.strip() for k in content.split(',') if k.strip()] 
                keywords = [k.strip() for k in matches if k.strip()]
                if keywords:
                    print(f"Recuperate {len(keywords)} keyword con fallback parsing da regex/split.")

            print(f"Generate {len(keywords)} keyword.")
            return keywords[:n_keywords]
            
        except json.JSONDecodeError as e:
            print(f"Errore di parsing JSON dalla risposta OpenAI: {e}. Contenuto: {content}")
            matches = re.findall(r'"([^"]+)"', content) 
            if not matches:
                 matches = [k.strip() for k in content.split(',') if k.strip()] 
            keywords = [k.strip() for k in matches if k.strip()]
            if keywords:
                print(f"Recuperate {len(keywords)} keyword con fallback parsing da regex/split.")
                return keywords[:n_keywords]
            return []
        except ValueError as e:
            print(f"Errore nella struttura dei dati JSON dalla risposta OpenAI: {e}. Contenuto: {content}")
            return []
            
    except openai.APIError as e:
        print(f"Errore API OpenAI durante la generazione keyword: {e}. Codice: {e.status_code}")
        if e.status_code == 429:
            print("Potrebbe essere un limite di rate/crediti API. Controlla il tuo account OpenAI.")
        return []
    except Exception as e:
        print(f"Errore generico durante la generazione keyword: {e}")
        return []

def genera_articolo(dati: dict, keyword: str, tema_generale: str) -> dict: 
    """
    Scrive un articolo SEO di 600 parole basato su una keyword specifica
    e sul tema generale dell'azienda.
    Restituisce un dizionario con titolo, sottotitolo e contenuto.
    """
    chi = dati.get('chi', 'un\'azienda')
    cosa = dati.get('cosa', 'servizi e prodotti')
    forza = dati.get('punti di forza', 'qualità e innovazione') 

    prompt = f"""
    Sei un copywriter SEO professionista ed esperto, specializzato nella creazione di contenuti di valore e ottimizzati per i motori di ricerca.
    Il tuo compito è scrivere un articolo SEO dettagliato e coinvolgente di circa 600 parole.
    
    L'articolo è per un'azienda di nome '{chi}' che opera nel settore di '{cosa}'.
    Il tema generale dell'azienda è '{tema_generale}'.
    La keyword principale per questo articolo è: '{keyword}'.
    
    L'articolo deve includere:
    1. Un paragrafo introduttivo che catturi l'attenzione e introduca il tema.
    2. Diversi paragrafi che approfondiscono la keyword, esplorando benefici, soluzioni,
       casi d'uso o aspetti rilevanti per l'azienda.
    3. Assicurati che la keyword '{keyword}' sia ripetuta naturalmente almeno 5-7 volte nel testo.
    4. Fai riferimento ai punti di forza dell'azienda, come '{forza}'.
    5. Concludi con un paragrafo riassuntivo e una chiara call to action. La Call to Action deve essere specifica e persuasiva, invitando il lettore a visitare il sito, contattare l'azienda, o scoprire di più sui servizi/prodotti.
    
    **Nuova istruzione per la struttura SEO interna (importante):**
    Il corpo dell'articolo (il valore della chiave "contenuto") deve essere formattato in HTML. Deve contenere, oltre ai paragrafi, la seguente struttura di intestazioni per il SEO. Queste intestazioni devono essere testi pertinenti ai sottotemi dell'articolo e devono includere la keyword dove appropriato, ma senza forzature.
    - Inizia il contenuto con un tag `<h2>` che sia il sottotitolo della prima sezione.
    - Includi esattamente altri due tag `<h3>` come sottosezioni del primo `<h2>`.
    - Includi esattamente un ulteriore tag `<h2>` per una nuova sezione principale.
    - Sotto il secondo `<h2>`, includi esattamente un tag `<h3>` per un dettaglio o una ulteriore suddivisione.
    - Assicurati di non usare mai un tag `<h1>` all'interno del campo "contenuto", dato che l'H1 principale della pagina è già fornito dal template.
    
    Esempio di struttura nel campo "contenuto":
    ```html
    <p>Paragrafo introduttivo...</p>
    <h2>Sottotitolo Principale 1: Tema Rilevante</h2>
    <p>Contenuto relativo al sottotitolo 1...</p>
    <h3>Sottosezione 1.1: Approfondimento</h3>
    <p>Contenuto dell'approfondimento...</p>
    <h3>Sottosezione 1.2: Caso Pratico</h3>
    <p>Contenuto del caso pratico...</p>
    <h2>Sottotitolo Principale 2: Benefici e Call to Action</h2>
    <p>Contenuto relativo al sottotitolo 2...</p>
    <h3>Dettaglio della Call to Action</h3>
    <p>Contenuto della call to action...</p>
    ```
    
    Stile: professionale, informativo, persuasivo, e orientato al valore per il lettore.
    
    Formato della risposta:
    Restituisci un oggetto JSON con le seguenti chiavi:
    {{
      "titolo": "Il titolo dell'articolo con la keyword",
      "sottotitolo": "Il sottotitolo esplicativo",
      "contenuto": "Il corpo dell'articolo di circa 600 parole formattato in HTML con H2, H3, H4 come richiesto."
    }}
    Assicurati che tutto il contenuto dell'articolo sia nella chiave "contenuto".
    """
    
    print(f"Generazione articolo per la keyword: '{keyword}'...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": "Sei un copywriter SEO professionista ed esperto, specializzato nella creazione di contenuti di valore e ottimizzati per i motori di ricerca. Rispondi solo in formato JSON come richiesto e includi i tag HTML H2, H3, H4 all'interno del contenuto come specificato, senza H1."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"} 
        )
        
        content_json_str = response.choices[0].message.content
        print(f"Risposta raw da OpenAI per articolo ('{keyword}'): {content_json_str[:200]}...") 
        
        try:
            parsed_article = json.loads(content_json_str)
            if not all(k in parsed_article for k in ["titolo", "sottotitolo", "contenuto"]):
                raise ValueError("JSON dell'articolo malformato o chiavi mancanti.")
            return parsed_article
        except json.JSONDecodeError as e:
            print(f"Errore di parsing JSON per l'articolo '{keyword}': {e}. Contenuto: {content_json_str}")
            return {
                "titolo": f"Articolo su {keyword}",
                "sottotitolo": "Contenuto generato con errore di formato.",
                "contenuto": content_json_str 
            }
    except openai.APIError as e:
        print(f"Errore API OpenAI durante la generazione articolo per '{keyword}': {e}")
        return {
            "titolo": f"Errore Articolo per {keyword}",
            "sottotitolo": "Generazione fallita",
            "contenuto": f"Si è verificato un errore durante la generazione dell'articolo per la keyword '{keyword}': {e}"
        }
    except Exception as e:
        print(f"Errore generico durante la generazione articolo per '{keyword}': {e}")
        return {
            "titolo": f"Errore Articolo per {keyword}",
            "sottotitolo": "Generazione fallita",
            "contenuto": f"Si è verificato un errore generico durante la generazione dell'articolo per la keyword '{keyword}': {e}"
        }


def genera_n_articoli(dati: dict, keywords: list, n_max: int = 20) -> list:
    """
    Genera N articoli basandosi su una lista di parole chiave fornite.
    Il tema generale sarà derivato dai dati dell'azienda.
    """
    articoli = []
    tema_generale = dati.get('cosa', dati.get('chi', 'servizi aziendali'))
    
    keywords_to_use = keywords[:n_max] 
    if not keywords_to_use:
        print("Nessuna keyword fornita per la generazione degli articoli.")
        return []

    print(f"Generazione di {len(keywords_to_use)} articoli basati su keyword specifiche.")
    for i, keyword in enumerate(keywords_to_use):
        print(f"Procedo con articolo {i+1}/{len(keywords_to_use)} per keyword: '{keyword}'")
        
        articolo_generato = genera_articolo(dati, keyword, tema_generale)
        
        articoli.append({
            "titolo": articolo_generato.get("titolo", f"Articolo su {keyword}"),
            "sottotitolo": articolo_generato.get("sottotitolo", ""),
            "keywords": keyword, 
            "contenuto": articolo_generato.get("contenuto", "")
        })
    return articoli