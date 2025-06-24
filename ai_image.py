import openai
import os
# from dotenv import load_dotenv # Rimosso: le credenziali saranno da variabili d'ambiente Cloud Build

# load_dotenv() # Rimosso

api_key_openai_img = os.getenv("OPENAI_API_KEY") # Useremo la stessa variabile di ai_content.py
if not api_key_openai_img:
    raise ValueError("La variabile d'ambiente OPENAI_API_KEY non trovata. Assicurati che Secret Manager e Cloud Build la forniscano.")

client_img = openai.OpenAI(api_key=api_key_openai_img)

def genera_immagine(prompt):
    print(f"Generazione immagine con DALL-E per prompt: '{prompt[:50]}...'")
    response = client_img.images.generate(
        model="dall-e-3", 
        prompt=prompt,
        n=1,
        size="1024x1024",
        response_format="url" 
    )
    print("Immagine DALL-E generata.")
    return response.data[0].url

