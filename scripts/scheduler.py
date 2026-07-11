"""
Orchestrator principal, rulat de GitHub Actions la fiecare rulare programata.

Calendar strategic:
- Postari simple: Luni si Vineri
- Carusele: Miercuri

Ce face, in ordine:
1. Verifica Google Drive pentru continut nou (postari simple + carusele).
2. Pentru intrarile "pending", genereaza imagine + caption -> "ready".
3. Pentru intrarile "ready" programate azi -> le publica pe Instagram.
"""
import itertools
import os
import re
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote

import content_calendar as cal
import google_drive as gdrive
import caption_generator as captions
import image_generator as imgen
import instagram_publisher as ig

# Zilele saptamanii (Luni=0 ... Duminica=6) pentru fiecare tip de postare.
SINGLE_POST_WEEKDAYS = {0, 4}   # Luni, Vineri
CAROUSEL_POST_WEEKDAYS = {2}    # Miercuri

RAW_GITHUB_BASE = os.environ.get(
    "RAW_GITHUB_BASE",
    "https://raw.githubusercontent.com/USERNAME/REPO/main",
)


def _slugify(name: str) -> str:
    """Inlocuieste spatiile si caracterele speciale, ca numele de fisier sa fie
    sigur intr-un URL (raw.githubusercontent.com nu accepta spatii neescapate)."""
    name = name.replace(" ", "-")
    return re.sub(r"[^A-Za-z0-9._-]", "", name)


def _next_slot(allowed_weekdays: set[int]) -> str:
    """Gaseste urmatoarea data libera (neocupata deja), cu ziua saptamanii
    permisa pentru acest tip de postare."""
    data = cal._load_raw()
    used_dates = {e["scheduled_date"] for e in data["entries"] if e["status"] != "failed"}

    candidate = date.today()
    for _ in range(60):  # limita de siguranta, ~2 luni inainte
        if candidate.weekday() in allowed_weekdays and candidate.isoformat() not in used_dates:
            return candidate.isoformat()
        candidate += timedelta(days=1)
    raise RuntimeError("Nu s-a gasit niciun slot liber in urmatoarele 60 de zile.")


def _image_url_for(local_path: Path) -> str:
    subfolder = "generated" if local_path.parent.name == "generated" else "incoming"
    return f"{RAW_GITHUB_BASE}/data/{subfolder}/{quote(local_path.name)}"


def step_1_ingest_new_content():
    print("-> Verific Google Drive pentru continut nou...")
    pillar_cycle = itertools.cycle(cal.CONTENT_PILLARS)

    # 1a. Postari simple (imagini din folderul principal) -> Luni/Vineri
    already_used = cal.already_used_image_ids()
    new_images = gdrive.list_new_single_images(already_used)
    for img in new_images:
        slot = _next_slot(SINGLE_POST_WEEKDAYS)
        pillar = next(pillar_cycle)
        cal.add_entry(
            source_image_id=img["id"],
            source_image_name=img["name"],
            pillar=pillar,
            scheduled_date=slot,
        )
        print(f"  + [single] {img['name']} -> {slot} ({pillar})")

    # 1b. Carusele (subfoldere din "carusele/") -> Miercuri
    already_used_folders = cal.already_used_folder_ids()
    new_carousels = gdrive.list_new_carousel_folders(already_used_folders)
    for folder in new_carousels:
        slot = _next_slot(CAROUSEL_POST_WEEKDAYS)
        pillar = next(pillar_cycle)
        image_ids = [f["id"] for f in folder["images"]]
        image_names = [f["name"] for f in folder["images"]]
        cal.add_carousel_entry(
            source_folder_id=folder["id"],
            source_folder_name=folder["name"],
            image_ids=image_ids,
            image_names=image_names,
            pillar=pillar,
            scheduled_date=slot,
        )
        print(f"  + [carusel] {folder['name']} ({len(image_ids)} imagini) -> {slot} ({pillar})")

    if not (new_images or new_carousels):
        print("  Niciun continut nou.")


def _prepare_single(entry: dict):
    local_path = gdrive.download_image(entry["source_image_id"], _slugify(entry["source_image_name"]))
    try:
        generated_path = imgen.generate_variation(local_path, "feed_square")
    except Exception as gen_error:
        print(f"  ! Generare varianta esuata, folosesc imaginea originala: {gen_error}")
        generated_path = local_path

    image_description = f"Randare/proiect de design interior: {entry['source_image_name']}"
    caption = captions.generate_caption(entry["pillar"], image_description)

    cal.update_entry(
        entry["id"],
        status="ready",
        caption=caption,
        generated_image_path=str(generated_path),
    )


def _prepare_carousel(entry: dict):
    local_paths = []
    folder_slug = _slugify(entry["source_folder_name"])
    for img_id, img_name in zip(entry["source_image_ids"], entry["source_image_names"]):
        prefixed_name = f"{folder_slug}_{_slugify(img_name)}"
        local_paths.append(gdrive.download_image(img_id, prefixed_name))

    image_description = (
        f"Set de {len(local_paths)} imagini din acelasi proiect de design interior "
        f"({entry['source_folder_name']})"
    )
    caption = captions.generate_caption(entry["pillar"], image_description)

    cal.update_entry(
        entry["id"],
        status="ready",
        caption=caption,
        generated_image_paths=[str(p) for p in local_paths],
    )


def step_2_prepare_pending_entries():
    print("-> Pregatesc intrarile in asteptare (imagine + caption)...")
    pending = cal.get_pending_entries()

    for entry in pending:
        try:
            post_type = entry.get("post_type", "single")
            if post_type == "single":
                _prepare_single(entry)
            elif post_type == "carousel":
                _prepare_carousel(entry)
            else:
                raise ValueError(f"post_type necunoscut: {post_type}")
            print(f"  OK pregatit [{post_type}] {entry.get('source_image_name') or entry.get('source_folder_name')}")
        except Exception as e:
            cal.mark_failed(entry["id"], str(e))
            print(f"  EROARE la pregatire: {e}")


def step_3_publish_due_posts():
    print("-> Verific postarile programate pentru azi...")
    due = cal.get_entries_due_today()
    ready_due = [e for e in due if e["status"] == "ready"]

    if not ready_due:
        print("  Nimic de postat azi.")
        return

    for entry in ready_due:
        try:
            post_type = entry.get("post_type", "single")

            if post_type == "single":
                image_url = _image_url_for(Path(entry["generated_image_path"]))
                media_id = ig.publish_image_post(image_url, entry["caption"])

            elif post_type == "carousel":
                image_urls = [_image_url_for(Path(p)) for p in entry["generated_image_paths"]]
                media_id = ig.publish_carousel_post(image_urls, entry["caption"])

            else:
                raise ValueError(f"post_type necunoscut: {post_type}")

            cal.mark_posted(entry["id"], media_id)
            print(f"  OK postat [{post_type}] media_id={media_id}")
        except Exception as e:
            cal.mark_failed(entry["id"], str(e))
            print(f"  EROARE la postare: {e}")


if __name__ == "__main__":
    step_1_ingest_new_content()
    step_2_prepare_pending_entries()
    step_3_publish_due_posts()
