"""
Genereaza caption-uri in romana, in stilul tau: storytelling emotional,
nu descrieri tehnice de rendering. Tematica e informativa, orientata spre
trafic si generare de leaduri (nu before/after, care presupune perechi de
imagini pe care nu le controlam in acest flux).
"""
import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

PILLAR_ANGLES = {
    "practical_tip": (
        "Un sfat practic, concret, de design interior, pornind de la ce se "
        "vede in imagine (culori, materiale, iluminat, organizarea spatiului). "
        "Trebuie sa fie util de sine statator, nu doar o descriere a pozei."
    ),
    "material_spotlight": (
        "Un focus educativ pe un material sau finisaj vizibil in imagine: "
        "de ce se alege, ce avantaje practice are, cum se intretine sau in ce "
        "tip de spatiu functioneaza cel mai bine."
    ),
    "design_process": (
        "O perspectiva din culise despre cum se ia o decizie de design sau "
        "ce presupune un proiect asemanator celui din imagine - un pas real "
        "din procesul tau de lucru, nu doar o descriere a rezultatului final."
    ),
    "myth_vs_reality": (
        "Corecteaza o presupunere gresita comuna despre design interior, "
        "legata de ce se vede in imagine (ex: un material considerat gresit "
        "'greu de intretinut', o culoare 'prea inchisa pentru spatii mici', etc). "
        "Ton lejer, nu didactic."
    ),
    "project_invitation": (
        "O postare direct informativa despre ce oferi ca serviciu, folosind "
        "imaginea ca punct de plecare, cu o invitatie clara catre un proiect "
        "nou. Nu suna a reclama agresiva, ci a o oferta genuina si calda."
    ),
}

SYSTEM_PROMPT = """Esti un copywriter specializat in continut pentru Instagram/TikTok \
pentru un brand de design interior si arhitectura (bmdesign.ro, Bogdan). \
Scrii exclusiv in romana, ton cald, storytelling, NU descrieri tehnice de \
rendering sau termeni de arhitect (perspectiva, randare fotorealista etc. \
se evita in caption, publicul e larg, nu breasla).

Continutul e informativ si orientat spre generarea de trafic si leaduri, \
NU spre before/after (nu presupunem ca avem o pereche de imagini).

Reguli stricte de stil:
- Caption scurt-mediu (3-6 randuri), nu eseu.
- Ton conversational, ca si cum povestesti sau explici unui prieten, nu ca o reclama.
- CTA orientat spre lead-uri, bazat pe comentarii: invita cititorul sa comenteze \
un cuvant/o intrebare care arata interes real pentru un proiect propriu \
(ex: "Comenteaza 'proiect' daca vrei ceva similar" sau o intrebare care \
invita raspunsuri legate de propriul spatiu al cititorului). \
NU "Acceseaza linkul din bio" (asta strica reach-ul organic).
- Maxim 3-5 hashtag-uri relevante la final, nu 20.
- Nu folosesti emoji in exces, 1-3 maxim, natural.
- Nu inventezi detalii tehnice false despre proiect (materiale, dimensiuni).

Raspunde DOAR cu caption-ul final, fara preambul, fara explicatii."""


def generate_caption(pillar: str, image_description: str) -> str:
    angle = PILLAR_ANGLES.get(pillar, PILLAR_ANGLES["practical_tip"])

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
