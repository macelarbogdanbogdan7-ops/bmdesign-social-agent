"""
Publica postari pe Instagram prin Instagram API (Instagram Login flow).
Suporta 2 tipuri de postari (imagine simpla, carusel) + gestionare
comentarii si mesaje directe (DM) pentru Modulul 3 (raspuns automat la leaduri).

IMPORTANT: Foloseste graph.instagram.com (nu graph.facebook.com), pentru ca
token-ul e generat prin fluxul Instagram Business Login, nu Facebook Login.
Graph API cere URL-uri publice catre imagini, nu upload direct de fisiere.

Necesita (vezi .env.example):
- IG_ACCESS_TOKEN, IG_BUSINESS_ACCOUNT_ID

Limite de retinut (Meta, 2026):
- Max 100 postari publicate prin API la 24h per cont (carusel = 1 postare).
- 200 apeluri/ora per aplicatie.
- 200 DM-uri automate/ora per cont.
"""
import os
import time
import requests

GRAPH_API_VERSION = "v21.0"
GRAPH_BASE = f"https://graph.instagram.com/{GRAPH_API_VERSION}"


def _access_token() -> str:
    return os.environ["IG_ACCESS_TOKEN"]


def _account_id() -> str:
    return os.environ["IG_BUSINESS_ACCOUNT_ID"]


def _wait_until_finished(container_id: str, token: str) -> None:
    status = "IN_PROGRESS"
    for _ in range(30):
        check = requests.get(
            f"{GRAPH_BASE}/{container_id}",
            params={"fields": "status_code", "access_token": token},
        )
        check.raise_for_status()
        status = check.json().get("status_code")
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise RuntimeError(f"Containerul media {container_id} a esuat.")
        time.sleep(6)
    raise TimeoutError(f"Containerul {container_id} nu s-a procesat la timp.")


def publish_image_post(image_url: str, caption: str) -> str:
    """Postare simpla, o singura imagine."""
    account_id = _account_id()
    token = _access_token()

    container_resp = requests.post(
        f"{GRAPH_BASE}/{account_id}/media",
        data={"image_url": image_url, "caption": caption, "access_token": token},
    )
    container_resp.raise_for_status()
    container_id = container_resp.json()["id"]

    _wait_until_finished(container_id, token)

    publish_resp = requests.post(
        f"{GRAPH_BASE}/{account_id}/media_publish",
        data={"creation_id": container_id, "access_token": token},
    )
    publish_resp.raise_for_status()
    return publish_resp.json()["id"]


def publish_carousel_post(image_urls: list[str], caption: str) -> str:
    """Postare tip carusel din 2-10 imagini."""
    account_id = _account_id()
    token = _access_token()

    if not (2 <= len(image_urls) <= 10):
        raise ValueError("Un carusel trebuie sa aiba intre 2 si 10 imagini.")

    child_ids = []
    for url in image_urls:
        child_resp = requests.post(
            f"{GRAPH_BASE}/{account_id}/media",
            data={"image_url": url, "is_carousel_item": "true", "access_token": token},
        )
        child_resp.raise_for_status()
        child_ids.append(child_resp.json()["id"])

    carousel_resp = requests.post(
        f"{GRAPH_BASE}/{account_id}/media",
        data={
            "media_type": "CAROUSEL",
            "children": ",".join(child_ids),
            "caption": caption,
            "access_token": token,
        },
    )
    carousel_resp.raise_for_status()
    container_id = carousel_resp.json()["id"]

    _wait_until_finished(container_id, token)

    publish_resp = requests.post(
        f"{GRAPH_BASE}/{account_id}/media_publish",
        data={"creation_id": container_id, "access_token": token},
    )
    publish_resp.raise_for_status()
    return publish_resp.json()["id"]


# ---------------------------------------------------------------------------
# Comentarii
# ---------------------------------------------------------------------------

def list_recent_media(limit: int = 15) -> list[dict]:
    """Ultimele postari publicate (id, caption, timestamp, comments_count),
    pentru a le verifica comentariile."""
    token = _access_token()
    account_id = _account_id()
    resp = requests.get(
        f"{GRAPH_BASE}/{account_id}/media",
        params={
            "fields": "id,caption,timestamp,comments_count",
            "limit": limit,
            "access_token": token,
        },
    )
    resp.raise_for_status()
    return resp.json().get("data", [])


def get_recent_comments(media_id: str) -> list[dict]:
    token = _access_token()
    resp = requests.get(
        f"{GRAPH_BASE}/{media_id}/comments",
        params={
            "fields": "id,text,username,timestamp,from",
            "access_token": token,
        },
    )
    resp.raise_for_status()
    return resp.json().get("data", [])


def post_comment(media_id: str, message: str) -> str:
    """Posteaza un comentariu nou (de pe contul propriu) pe o postare.
    Util pentru demo App Review: scrierea proprie functioneaza fara
    Advanced Access, spre deosebire de citirea comentariilor altor useri."""
    token = _access_token()
    resp = requests.post(
        f"{GRAPH_BASE}/{media_id}/comments",
        data={"message": message, "access_token": token},
    )
    resp.raise_for_status()
    return resp.json()["id"]


def reply_to_comment(comment_id: str, message: str) -> str:
    token = _access_token()
    resp = requests.post(
        f"{GRAPH_BASE}/{comment_id}/replies",
        data={"message": message, "access_token": token},
    )
    resp.raise_for_status()
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# Mesaje directe (DM)
# ---------------------------------------------------------------------------

def list_conversations(limit: int = 20) -> list[dict]:
    """Conversatiile recente de Direct Message."""
    token = _access_token()
    account_id = _account_id()
    resp = requests.get(
        f"{GRAPH_BASE}/{account_id}/conversations",
        params={"platform": "instagram", "limit": limit, "access_token": token},
    )
    resp.raise_for_status()
    return resp.json().get("data", [])


def get_conversation_messages(conversation_id: str, limit: int = 10) -> list[dict]:
    """Ultimele mesaje dintr-o conversatie (id, from, message/text, created_time)."""
    token = _access_token()
    resp = requests.get(
        f"{GRAPH_BASE}/{conversation_id}",
        params={
            "fields": f"messages.limit({limit}){{id,from,to,message,created_time}}",
            "access_token": token,
        },
    )
    resp.raise_for_status()
    return resp.json().get("messages", {}).get("data", [])


def send_dm(recipient_id: str, message: str) -> str:
    """Trimite un mesaj direct catre un utilizator (recipient_id = PSID/IGSID)."""
    token = _access_token()
    account_id = _account_id()
    resp = requests.post(
        f"{GRAPH_BASE}/{account_id}/messages",
        json={
            "recipient": {"id": recipient_id},
            "message": {"text": message},
        },
        params={"access_token": token},
    )
    resp.raise_for_status()
    return resp.json().get("message_id", "")
