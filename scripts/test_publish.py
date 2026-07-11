"""
Script de test, unic, pentru a verifica publicarea directa prin Instagram
API. Afiseaza raspunsul complet de eroare de la Meta, pentru diagnostic.
"""
import os
import requests

IMAGE_URL = "https://raw.githubusercontent.com/macelarbogdanbogdan7-ops/bmdesign-social-agent/main/data/incoming/Image_with_logo.png"

CAPTION = """O bucatarie care nu se ascunde.

Cupru cald, marmura neagra cu vene aurii si accente rosii care par desprinse dintr-o poveste - aici fiecare detaliu are personalitate, nu doar functie.

Tu ai alege un asemenea contrast in propria bucatarie, sau preferi tonuri mai discrete? Spune-mi in comentarii.

#designinterior #bucatariemoderna #cupru #arhitecturainterioara #bmdesign"""

GRAPH_BASE = "https://graph.instagram.com/v21.0"
account_id = os.environ["IG_BUSINESS_ACCOUNT_ID"]
token = os.environ["IG_ACCESS_TOKEN"]

print(f"Account ID: {account_id}")
print(f"Image URL: {IMAGE_URL}")

resp = requests.post(
    f"{GRAPH_BASE}/{account_id}/media",
    data={
        "image_url": IMAGE_URL,
        "caption": CAPTION,
        "access_token": token,
    },
)

print(f"Status code: {resp.status_code}")
print(f"Response body: {resp.text}")
