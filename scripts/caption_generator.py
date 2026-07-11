"""
Genereaza caption-uri in romana, in stilul tau: storytelling emotional,
nu descrieri tehnice de rendering. CTA bazat pe comentarii (pentru reach
algoritmic), nu link-uri directe in caption.
"""
import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

PILLAR_ANGLES = {
      "before_after": (
                "O transformare vizuala: cum arata spatiul inainte si cum arata "
                "randarea/proiectul acum. Accent pe emotia schimbarii."
      ),
      "process": (
                "Din culise: un pas din procesul tau de proiectare, cum iei o "
                "decizie, cum alegi materialele, cum rezolvi o provocare de spatiu."
      ),
      "storytelling": (
                "O poveste emotionala legata de proiect, ex. un cuplu cu gusturi "
                "diferite care gaseste un compromis, o familie care isi doreste "
                "un anumit colt al casei pentru un anumit motiv."
      ),
      "tips": (
                "Un sfat scurt, practic, de design interior legat de ce se vede "
                "in imagine (culori, materiale, iluminat)."
      ),
      "material_focus": (
                "Focus pe un material sau detaliu specific din imagine, textura, "
                "de ce a fost ales, ce senzatie transmite."
      ),
}

SYSTEM_PROMPT = """Esti un copywriter specializat in continut pentru Instagram/TikTok \
pentru un brand de design interior si arhitectura (bmdesign.ro, Bogdan). \
Scrii exclusiv in romana, ton cald, storytelling, NU descrieri tehnice de \
rendering sau termeni de arhitect (perspectiva, randare fotorealista etc. \
se evita in caption, publicul e larg, nu breasla).

Reguli stricte de stil:
- Caption scurt-mediu (3-6 randuri), nu eseu.
- Ton conversational, ca si cum povestesti, nu ca o reclama.
- CTA bazat pe comentarii, gen "Comenteaza X daca..." sau o intrebare care \
invita raspunsuri, NU "Acceseaza linkul din bio" (asta strica reach-ul organic).
- Maxim 3-5 hashtag-uri relevante la final, nu 20.
- Nu folosesti emoji in exces, 1-3 maxim, natural.
- Nu inventezi detalii tehnice false despre proiect (materiale, dimensiuni).

Raspunde DOAR cu caption-ul final, fara preambul, fara explicatii."""


def generate_caption(pillar: str, image_description: str) -> str:
      angle = PILLAR_ANGLES.get(pillar, PILLAR_ANGLES["storytelling"])

    user_prompt = f"""Unghiul postarii: {angle}

    Descrierea imaginii/proiectului: {image_description}

    Scrie caption-ul pentru aceasta postare."""

    response = client.messages.create(
              model="claude-sonnet-4-6",
              max_tokens=400,
              system=SYSTEM_PROMPT,
              messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text.strip()
