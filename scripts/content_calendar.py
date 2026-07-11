"""
Gestioneaza calendarul de continut: o lista de "intrari" (postari) salvate
intr-un fisier JSON care persista in repo (commit automat de GitHub Actions
dupa fiecare rulare).

Fiecare intrare are un status: pending -> ready -> posted (sau failed), si un
post_type: "single" | "carousel" | "story".
"""
import json
import uuid
from datetime import date, datetime
from pathlib import Path

CALENDAR_PATH = Path(__file__).parent.parent / "data" / "calendar.json"

# Pilonii tematici de continut - informativi + generare de trafic/leaduri.
CONTENT_PILLARS = [
    "practical_tip",
    "material_spotlight",
    "design_process",
    "myth_vs_reality",
    "project_invitation",
]


def _load_raw() -> dict:
    if not CALENDAR_PATH.exists():
        return {"entries": []}
    with open(CALENDAR_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_raw(data: dict) -> None:
    CALENDAR_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CALENDAR_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_entry(
    source_image_id: str,
    source_image_name: str,
    pillar: str,
    scheduled_date: str,
) -> dict:
    """Postare simpla (o singura imagine)."""
    data = _load_raw()
    entry = {
        "id": str(uuid.uuid4()),
        "status": "pending",
        "post_type": "single",
        "pillar": pillar,
        "scheduled_date": scheduled_date,
        "source_image_id": source_image_id,
        "source_image_name": source_image_name,
        "generated_image_path": None,
        "caption": None,
        "created_at": datetime.utcnow().isoformat(),
        "posted_at": None,
        "ig_media_id": None,
        "error": None,
    }
    data["entries"].append(entry)
    _save_raw(data)
    return entry


def add_carousel_entry(
    source_folder_id: str,
    source_folder_name: str,
    image_ids: list[str],
    image_names: list[str],
    pillar: str,
    scheduled_date: str,
) -> dict:
    """Postare tip carusel (2-10 imagini dintr-un subfolder dedicat)."""
    data = _load_raw()
    entry = {
        "id": str(uuid.uuid4()),
        "status": "pending",
        "post_type": "carousel",
        "pillar": pillar,
        "scheduled_date": scheduled_date,
        "source_folder_id": source_folder_id,
        "source_folder_name": source_folder_name,
        "source_image_ids": image_ids,
        "source_image_names": image_names,
        "generated_image_paths": None,
        "caption": None,
        "created_at": datetime.utcnow().isoformat(),
        "posted_at": None,
        "ig_media_id": None,
        "error": None,
    }
    data["entries"].append(entry)
    _save_raw(data)
    return entry


def add_story_entry(
    source_image_id: str,
    source_image_name: str,
    scheduled_date: str,
) -> dict:
    """Postare tip Story (fara caption, expira in 24h pe Instagram)."""
    data = _load_raw()
    entry = {
        "id": str(uuid.uuid4()),
        "status": "pending",
        "post_type": "story",
        "pillar": None,
        "scheduled_date": scheduled_date,
        "source_image_id": source_image_id,
        "source_image_name": source_image_name,
        "generated_image_path": None,
        "caption": None,
        "created_at": datetime.utcnow().isoformat(),
        "posted_at": None,
        "ig_media_id": None,
        "error": None,
    }
    data["entries"].append(entry)
    _save_raw(data)
    return entry


def get_entries_due_today() -> list[dict]:
    today = date.today().isoformat()
    data = _load_raw()
    return [
        e for e in data["entries"]
        if e["scheduled_date"] == today and e["status"] in ("pending", "ready")
    ]


def get_pending_entries() -> list[dict]:
    data = _load_raw()
    return [e for e in data["entries"] if e["status"] == "pending"]


def update_entry(entry_id: str, **fields) -> None:
    data = _load_raw()
    for e in data["entries"]:
        if e["id"] == entry_id:
            e.update(fields)
            break
    _save_raw(data)


def mark_posted(entry_id: str, ig_media_id: str) -> None:
    update_entry(
        entry_id,
        status="posted",
        ig_media_id=ig_media_id,
        posted_at=datetime.utcnow().isoformat(),
    )


def mark_failed(entry_id: str, error: str) -> None:
    update_entry(entry_id, status="failed", error=error)


def already_used_image_ids() -> set[str]:
    """Toate ID-urile de imagini deja folosite, indiferent de tipul postarii."""
    data = _load_raw()
    ids = set()
    for e in data["entries"]:
        if e.get("source_image_id"):
            ids.add(e["source_image_id"])
        if e.get("source_image_ids"):
            ids.update(e["source_image_ids"])
    return ids


def already_used_folder_ids() -> set[str]:
    """Subfolderele de carusel deja procesate (nu se reiau)."""
    data = _load_raw()
    return {e["source_folder_id"] for e in data["entries"] if e.get("source_folder_id")}
