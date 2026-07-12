"""
Modulul 3: detecteaza comentarii si DM-uri cu intentie de lead pe postarile
recente, si raspunde automat, cald si personalizat (Claude), complet fara
confirmare manuala.

Ruleaza separat de scheduler.py, pe un cron mai frecvent (vezi
.github/workflows/leads.yml), ca sa prinda interactiuni noi la timp scurt.

Retine ID-urile deja procesate in data/interactions.json, ca sa nu
raspunda de doua ori la acelasi comentariu/mesaj.
"""
import json
import os
from pathlib import Path

from anthropic import Anthropic

import instagram_publisher as ig

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

INTERACTIONS_PATH = Path(__file__).parent.parent / "data" / "interactions.json"

MEDIA_TO_CHECK = 15          # cate postari recente verificam pentru comentarii noi
CONVERSATIONS_TO_CHECK = 20  # cate conversatii DM recente verificam

CONTACT_FORM_URL = "https://bmdesign.ro/contact/"

COMMENT_SYSTEM_PROMPT = """Esti asistentul de social media al lui Bogdan, un \
designer de interior din Romania (bmdesign.ro). Cineva a lasat un comentariu \
public la o postare de-a lui pe Instagram. Analizeaza comentariul si decide \
daca arata intentie reala de lead (vrea un proiect similar, intreaba de \
pret/servicii, foloseste cuvantul cheie din CTA-ul postarii, cere mai multe \
detalii) sau e doar un comentariu generic (apreciere, emoji, ceva fara \
legatura).

Daca ESTE lead: scrie un raspuns public scurt (1-2 propozitii), cald, \
conversational, care multumeste pentru interes si il invita explicit sa \
trimita un DM pentru detalii (ex: "Iti trimit un mesaj acum!" sau "Scrie-mi \
te rog pe DM cu ce ai in minte"). NU discuta preturi, detalii tehnice sau \
link-uri in comentariul public.

Daca NU e lead: raspunsul poate fi un simplu multumesc scurt si cald, sau \
poate sa nu necesite deloc raspuns (in acest caz seteaza reply la null).

Raspunde STRICT in format JSON, fara alt text: \
{"is_lead": true/false, "reply": "text sau null"}"""

DM_SYSTEM_PROMPT = f"""Esti asistentul de social media al lui Bogdan, un designer \
de interior din Romania (bmdesign.ro). Cineva ti-a trimis un mesaj direct (DM) \
pe Instagram. Analizeaza mesajul si raspunde ca un om real, cald si prietenos, \
nu ca un bot corporate.

Daca mesajul arata interes real pentru un proiect de design interior: \
multumeste, arata entuziasm autentic, si include linkul catre formularul de \
contact ({CONTACT_FORM_URL}), invitandu-l cald sa completeze cateva detalii \
acolo (tip de spatiu, oras, ce isi doreste) ca Bogdan sa poata reveni personal \
cu un raspuns potrivit. NU promite preturi sau termene exacte (nu ai aceste \
informatii). Mentioneaza ca Bogdan revine personal dupa ce vede formularul.

Daca mesajul e generic, spam, sau fara legatura cu un proiect posibil: \
raspunde scurt si politicos, fara link, sau seteaza reply la null daca nu \
merita raspuns (ex: spam clar).

Raspunde STRICT in format JSON, fara alt text: \
{{"is_lead": true/false, "reply": "text sau null"}}"""


def _load_interactions() -> dict:
    if not INTERACTIONS_PATH.exists():
        return {"replied_comment_ids": [], "replied_message_ids": []}
    with open(INTERACTIONS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_interactions(data: dict) -> None:
    INTERACTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INTERACTIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _classify(system_prompt: str, text: str) -> dict:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=system_prompt,
        messages=[{"role": "user", "content": text}],
    )
    raw = response.content[0].text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"is_lead": False, "reply": None}


def process_comments():
    print("-> Verific comentarii noi pe postarile recente...")
    data = _load_interactions()
    replied_ids = set(data["replied_comment_ids"])

    media_list = ig.list_recent_media(limit=MEDIA_TO_CHECK)
    new_replies = 0

    for media in media_list:
        try:
            comments = ig.get_recent_comments(media["id"])
        except Exception as e:
            print(f"  ! Nu am putut citi comentariile pentru {media['id']}: {e}")
            continue

        for comment in comments:
            comment_id = comment["id"]
            if comment_id in replied_ids:
                continue

            text = comment.get("text", "")
            username = comment.get("username", "cineva")

            result = _classify(COMMENT_SYSTEM_PROMPT, text)
            replied_ids.add(comment_id)  # marcam procesat indiferent de rezultat

            if result.get("is_lead") and result.get("reply"):
                try:
                    ig.reply_to_comment(comment_id, result["reply"])
                    new_replies += 1
                    print(f"  OK raspuns la comentariul lui {username}: {text[:50]!r}")
                except Exception as e:
                    print(f"  ! Eroare la raspuns comentariu {comment_id}: {e}")

    data["replied_comment_ids"] = list(replied_ids)
    _save_interactions(data)
    print(f"  Total raspunsuri noi la comentarii: {new_replies}")


def process_dms():
    print("-> Verific mesaje directe (DM) noi...")
    data = _load_interactions()
    replied_ids = set(data["replied_message_ids"])
    account_id = os.environ["IG_BUSINESS_ACCOUNT_ID"]

    try:
        conversations = ig.list_conversations(limit=CONVERSATIONS_TO_CHECK)
    except Exception as e:
        print(f"  ! Nu am putut citi conversatiile: {e}")
        return

    new_replies = 0

    for convo in conversations:
        convo_id = convo["id"]
        try:
            messages = ig.get_conversation_messages(convo_id, limit=5)
        except Exception as e:
            print(f"  ! Nu am putut citi mesajele din conversatia {convo_id}: {e}")
            continue

        for msg in messages:
            msg_id = msg.get("id")
            sender_id = msg.get("from", {}).get("id")

            if msg_id in replied_ids or sender_id == account_id:
                continue  # deja procesat, sau e un mesaj trimis chiar de noi

            text = msg.get("message", "")
            if not text:
                replied_ids.add(msg_id)
                continue

            result = _classify(DM_SYSTEM_PROMPT, text)
            replied_ids.add(msg_id)

            if result.get("reply"):
                try:
                    ig.send_dm(sender_id, result["reply"])
                    new_replies += 1
                    print(f"  OK raspuns DM catre {sender_id}: {text[:50]!r}")
                except Exception as e:
                    print(f"  ! Eroare la raspuns DM catre {sender_id}: {e}")

    data["replied_message_ids"] = list(replied_ids)
    _save_interactions(data)
    print(f"  Total raspunsuri noi la DM-uri: {new_replies}")


if __name__ == "__main__":
    process_comments()
    process_dms()
"""
Modulul 3: detecteaza comentarii si DM-uri cu intentie de lead pe postarile
recente, si raspunde automat, cald si personalizat (Claude), complet fara
confirmare manuala.

Ruleaza separat de scheduler.py, pe un cron mai frecvent (vezi
.github/workflows/leads.yml), ca sa prinda interactiuni noi la timp scurt.

Retine ID-urile deja procesate in data/interactions.json, ca sa nu
raspunda de doua ori la acelasi comentariu/mesaj.
"""
import json
import os
from pathlib import Path

from anthropic import Anthropic

import instagram_publisher as ig

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

INTERACTIONS_PATH = Path(__file__).parent.parent / "data" / "interactions.json"

MEDIA_TO_CHECK = 15          # cate postari recente verificam pentru comentarii noi
CONVERSATIONS_TO_CHECK = 20  # cate conversatii DM recente verificam

COMMENT_SYSTEM_PROMPT = """Esti asistentul de social media al lui Bogdan, un \
designer de interior din Romania (bmdesign.ro). Cineva a lasat un comentariu \
public la o postare de-a lui pe Instagram. Analizeaza comentariul si decide \
daca arata intentie reala de lead (vrea un proiect similar, intreaba de \
pret/servicii, foloseste cuvantul cheie din CTA-ul postarii, cere mai multe \
detalii) sau e doar un comentariu generic (apreciere, emoji, ceva fara \
legatura).

Daca ESTE lead: scrie un raspuns public scurt (1-2 propozitii), cald, \
conversational, care multumeste pentru interes si il invita explicit sa \
trimita un DM pentru detalii (ex: "Iti trimit un mesaj acum!" sau "Scrie-mi \
te rog pe DM cu ce ai in minte"). NU discuta preturi sau detalii tehnice \
in comentariul public.

Daca NU e lead: raspunsul poate fi un simplu multumesc scurt si cald, sau \
poate sa nu necesite deloc raspuns (in acest caz seteaza reply la null).

Raspunde STRICT in format JSON, fara alt text: \
{"is_lead": true/false, "reply": "text sau null"}"""

DM_SYSTEM_PROMPT = """Esti asistentul de social media al lui Bogdan, un designer \
de interior din Romania (bmdesign.ro). Cineva ti-a trimis un mesaj direct (DM) \
pe Instagram. Analizeaza mesajul si raspunde ca un om real, cald si prietenos, \
nu ca un bot corporate.

Daca mesajul arata interes real pentru un proiect de design interior: \
multumeste, arata entuziasm autentic, si pune O SINGURA intrebare de \
calificare naturala (ex: ce tip de spatiu, ce oras/zona, sau ce il-a atras \
la proiectele lui) - nu un chestionar. NU promite preturi sau termene exacte \
(nu ai aceste informatii). Poti mentiona ca Bogdan revine personal cu \
detalii daca discutia devine specifica.

Daca mesajul e generic, spam, sau fara legatura cu un proiect posibil: \
raspunde scurt si politicos, sau seteaza reply la null daca nu merita \
raspuns (ex: spam clar).

Raspunde STRICT in format JSON, fara alt text: \
{"is_lead": true/false, "reply": "text sau null"}"""


def _load_interactions() -> dict:
    if not INTERACTIONS_PATH.exists():
        return {"replied_comment_ids": [], "replied_message_ids": []}
    with open(INTERACTIONS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_interactions(data: dict) -> None:
    INTERACTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INTERACTIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _classify(system_prompt: str, text: str) -> dict:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=system_prompt,
        messages=[{"role": "user", "content": text}],
    )
    raw = response.content[0].text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"is_lead": False, "reply": None}


def process_comments():
    print("-> Verific comentarii noi pe postarile recente...")
    data = _load_interactions()
    replied_ids = set(data["replied_comment_ids"])

    media_list = ig.list_recent_media(limit=MEDIA_TO_CHECK)
    print(f"  [debug] Postari recente gasite: {len(media_list)}")
    new_replies = 0

    for media in media_list:
        reported_count = media.get("comments_count", "?")
        try:
            comments = ig.get_recent_comments(media["id"])
        except Exception as e:
            print(f"  ! Nu am putut citi comentariile pentru {media['id']}: {e}")
            continue

        print(f"  [debug] Media {media['id']}: comments_count raportat de Meta={reported_count}, primite prin API={len(comments)}")

        for comment in comments:
            comment_id = comment["id"]
            if comment_id in replied_ids:
                continue

            text = comment.get("text", "")
            username = comment.get("username", "cineva")
            print(f"  [debug] Comentariu nou de la {username}: {text!r}")

            result = _classify(COMMENT_SYSTEM_PROMPT, text)
            replied_ids.add(comment_id)  # marcam procesat indiferent de rezultat
            print(f"  [debug] Clasificare: {result}")

            if result.get("is_lead") and result.get("reply"):
                try:
                    ig.reply_to_comment(comment_id, result["reply"])
                    new_replies += 1
                    print(f"  OK raspuns la comentariul lui {username}: {text[:50]!r}")
                except Exception as e:
                    print(f"  ! Eroare la raspuns comentariu {comment_id}: {e}")

    data["replied_comment_ids"] = list(replied_ids)
    _save_interactions(data)
    print(f"  Total raspunsuri noi la comentarii: {new_replies}")


def process_dms():
    print("-> Verific mesaje directe (DM) noi...")
    data = _load_interactions()
    replied_ids = set(data["replied_message_ids"])
    account_id = os.environ["IG_BUSINESS_ACCOUNT_ID"]

    try:
        conversations = ig.list_conversations(limit=CONVERSATIONS_TO_CHECK)
    except Exception as e:
        print(f"  ! Nu am putut citi conversatiile: {e}")
        return

    print(f"  [debug] Conversatii gasite: {len(conversations)}")
    new_replies = 0

    for convo in conversations:
        convo_id = convo["id"]
        try:
            messages = ig.get_conversation_messages(convo_id, limit=5)
        except Exception as e:
            print(f"  ! Nu am putut citi mesajele din conversatia {convo_id}: {e}")
            continue

        print(f"  [debug] Conversatia {convo_id}: {len(messages)} mesaje")

        for msg in messages:
            msg_id = msg.get("id")
            sender_id = msg.get("from", {}).get("id")

            if msg_id in replied_ids or sender_id == account_id:
                continue  # deja procesat, sau e un mesaj trimis chiar de noi

            text = msg.get("message", "")
            if not text:
                replied_ids.add(msg_id)
                continue

            print(f"  [debug] Mesaj nou de la {sender_id}: {text!r}")
            result = _classify(DM_SYSTEM_PROMPT, text)
            replied_ids.add(msg_id)
            print(f"  [debug] Clasificare: {result}")

            if result.get("reply"):
                try:
                    ig.send_dm(sender_id, result["reply"])
                    new_replies += 1
                    print(f"  OK raspuns DM catre {sender_id}: {text[:50]!r}")
                except Exception as e:
                    print(f"  ! Eroare la raspuns DM catre {sender_id}: {e}")

    data["replied_message_ids"] = list(replied_ids)
    _save_interactions(data)
    print(f"  Total raspunsuri noi la DM-uri: {new_replies}")


if __name__ == "__main__":
    process_comments()
    process_dms()
