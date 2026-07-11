"""
Publica postari pe Instagram prin Graph API (Content Publishing flow).

IMPORTANT: Graph API cere un URL public catre imagine, nu upload direct de
fisier. Cea mai simpla solutie fara server: imaginile generate se pun in
repo (/data/incoming sau /data/generated), GitHub Actions le comite, iar
Graph API le preia de la adresa raw.githubusercontent.com.

Necesita (vezi .env.example):
- IG_ACCESS_TOKEN: token long-lived, cu permisiunile instagram_content_publish
  si instagram_basic aprobate prin App Review.
  - IG_BUSINESS_ACCOUNT_ID: ID-ul contului tau Business/Creator.

  Limite de retinut (Meta, 2026):
  - Max 100 postari publicate prin API la 24h per cont.
  - 200 apeluri/ora per aplicatie.
  """
import os
import time
import requests

GRAPH_API_VERSION = "v21.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def _access_token() -> str:
      return os.environ["IG_ACCESS_TOKEN"]


def _account_id() -> str:
      return os.environ["IG_BUSINESS_ACCOUNT_ID"]


def publish_image_post(image_url: str, caption: str) -> str:
      account_id = _account_id()
      token = _access_token()

    container_resp = requests.post(
              f"{GRAPH_BASE}/{account_id}/media",
              data={
                            "image_url": image_url,
                            "caption": caption,
                            "access_token": token,
              },
    )
    container_resp.raise_for_status()
    container_id = container_resp.json()["id"]

    status = "IN_PROGRESS"
    for _ in range(20):
              check = requests.get(
                            f"{GRAPH_BASE}/{container_id}",
                            params={"fields": "status_code", "access_token": token},
              )
              check.raise_for_status()
              status = check.json().get("status_code")
              if status == "FINISHED":
                            break
                        if status == "ERROR":
                                      raise RuntimeError(f"Containerul media a esuat pentru {image_url}")
                                  time.sleep(6)

    if status != "FINISHED":
              raise TimeoutError("Containerul media nu s-a procesat la timp.")

    publish_resp = requests.post(
              f"{GRAPH_BASE}/{account_id}/media_publish",
              data={"creation_id": container_id, "access_token": token},
    )
    publish_resp.raise_for_status()
    return publish_resp.json()["id"]


def get_recent_comments(media_id: str) -> list[dict]:
      token = _access_token()
    resp = requests.get(
              f"{GRAPH_BASE}/{media_id}/comments",
              params={"fields": "id,text,username,timestamp", "access_token": token},
    )
    resp.raise_for_status()
    return resp.json().get("data", [])


def reply_to_comment(comment_id: str, message: str) -> str:
      token = _access_token()
    resp = requests.post(
              f"{GRAPH_BASE}/{comment_id}/replies",
              data={"message": message, "access_token": token},
    )
    resp.raise_for_status()
    return resp.json()["id"]
