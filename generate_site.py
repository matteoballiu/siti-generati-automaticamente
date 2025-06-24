from jinja2 import Environment, FileSystemLoader

# Rimuovi l'inizializzazione globale di env qui. Verrà passata come argomento da run_automation.py.
# env = Environment(loader=FileSystemLoader('.'))

# Modificata la firma della funzione per accettare sidebar_img_url
def crea_pagina_articolo(jinja_env: Environment, titolo: str, sottotitolo: str, keywords: str, img_url: str, sidebar_img_url: str, contenuto: str, palette: dict, footer_data: dict) -> str:
    """
    Genera il contenuto HTML per una singola pagina articolo.
    Accetta l'ambiente Jinja2 come primo parametro.
    Aggiunto sidebar_img_url per l'immagine laterale.
    """
    template = jinja_env.get_template('article_template.html')
    return template.render(
        titolo=titolo,
        sottotitolo=sottotitolo,
        keywords=keywords,
        img_url=img_url,
        sidebar_img_url=sidebar_img_url, # Passa l'URL dell'immagine della sidebar al template
        contenuto=contenuto,
        palette=palette,
        footer_data=footer_data
    )

def crea_home_page(
    jinja_env: Environment,
    titolo: str,
    sottotitolo: str,
    keywords: str,
    img_url_home: str,
    home_content: str,
    articoli: list,
    palette: dict,
    footer_data: dict,
    social_urls: dict
) -> str:
    """
    Genera il contenuto HTML per la home page, che elenca gli articoli.
    Accetta l'ambiente Jinja2 come primo parametro.
    """
    template = jinja_env.get_template('home_template.html')
    return template.render(
        titolo=titolo,
        sottotitolo=sottotitolo,
        keywords=keywords,
        img_url_home=img_url_home,
        home_content=home_content,
        articoli=articoli,
        palette=palette,
        footer_data=footer_data,
        social_urls=social_urls
    )
