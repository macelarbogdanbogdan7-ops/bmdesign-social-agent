"""
Script de test, unic, pentru a verifica publicarea directa prin Instagram
API (Instagram Login flow, graph.instagram.com).
"""
import instagram_publisher as ig

IMAGE_URL = "https://raw.githubusercontent.com/macelarbogdanbogdan7-ops/bmdesign-social-agent/main/data/incoming/Image_with_logo.png"

CAPTION = """O bucatarie care nu se ascunde.

Cupru cald, marmura neagra cu vene aurii si accente rosii care par desprinse dintr-o poveste - aici fiecare detaliu are personalitate, nu doar functie.

Tu ai alege un asemenea contrast in propria bucatarie, sau preferi tonuri mai discrete? Spune-mi in comentarii.

#designinterior #bucatariemoderna #cupru #arhitecturainterioara #bmdesign"""

if __name__ == "__main__":
    media_id = ig.publish_image_post(IMAGE_URL, CAPTION)
    print(f"Postat cu succes. media_id={media_id}")
