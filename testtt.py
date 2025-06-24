import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")
try:
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Ciao"}]
    )
    print(resp.choices[0].message.content)
except Exception as e:
    print("Errore:", e)