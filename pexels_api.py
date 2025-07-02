# pexels_api.py
import os
import requests
# from dotenv import load_dotenv # Rimosso: le credenziali saranno da variabili d'ambiente Cloud Build
from pathlib import Path

# load_dotenv() # Rimosso

from typing import Optional  # mettilo in cima al file se non c’è


PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
if not PEXELS_API_KEY:
    raise ValueError("La variabile d'ambiente PEXELS_API_KEY non è stata impostata. Assicurati che Secret Manager e Cloud Build la forniscano.")

PEXELS_HEADERS = {"Authorization": PEXELS_API_KEY}
PEXELS_BASE_URL = "https://api.pexels.com/v1"

def cerca_e_scarica_immagine_pexels(query: str, save_path: Path, filename_prefix: str = "pexels_image", orientation: str = "landscape") -> Optional[str]:
    """
    Cerca un'immagine su Pexels in base a una query, la scarica e la salva localmente.
    Restituisce il percorso relativo al file salvato o None in caso di fallimento.
    """
    search_url = f"{PEXELS_BASE_URL}/search"
    params = {
        "query": query,
        "per_page": 1, 
        "orientation": orientation
    }

    print(f"Ricerca immagine su Pexels per query: '{query}'...")
    try:
        response = requests.get(search_url, headers=PEXELS_HEADERS, params=params)
        response.raise_for_status() 
        data = response.json()

        if data and data["photos"]:
            photo_url = data["photos"][0]["src"]["large"] 
            
            original_ext = Path(photo_url).suffix if Path(photo_url).suffix else ".jpeg"
            
            image_name = f"{filename_prefix}{original_ext}" 
            
            local_image_path = save_path / image_name

            save_path.mkdir(parents=True, exist_ok=True)

            print(f"Scaricando immagine da: {photo_url} a {local_image_path}")
            img_data = requests.get(photo_url, stream=True)
            img_data.raise_for_status()

            with open(local_image_path, 'wb') as f:
                for chunk in img_data.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Immagine Pexels salvata localmente in: {local_image_path}")
            return str(local_image_path.relative_to(Path("public").parent))
        else:
            print(f"Nessuna immagine trovata su Pexels per la query: '{query}'")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Errore durante la ricerca/download immagine da Pexels: {e}")
        return None
    except Exception as e:
        print(f"Errore generico in pexels_api: {e}")
        return None

if __name__ == "__main__":
    print("Test di ricerca e download immagine da Pexels...")
    test_output_dir = Path("test_images")
    test_output_dir.mkdir(exist_ok=True)

    query_test = "business technology"
    local_path = cerca_e_scarica_immagine_pexels(query_test, test_output_dir, filename_prefix="test_biz_tech_hash123")
    if local_path:
        print(f"Immagine di test scaricata con successo in: {local_path}")
    else:
        print("Impossibile scaricare immagine di test.")

    query_test_2 = "art gallery milan"
    local_path_2 = cerca_e_scarica_immagine_pexels(query_test_2, test_output_dir, filename_prefix="test_art_gallery_hash456")
    if local_path_2:
        print(f"Immagine di test 2 scaricata con successo in: {local_path_2}")
    else:
        print("Impossibile scaricare immagine di test 2.")