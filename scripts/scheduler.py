"""
Orchestrator principal, rulat de GitHub Actions la fiecare rulare programata.

Ce face, in ordine:
1. Verifica Google Drive pentru randari noi -> le adauga in calendar (pending).
2. Pentru intrarile "pending", genereaza caption -> le trece in "ready".
3. Pentru intrarile "ready" programate azi -> le publica pe Instagram.

Nota: generarea de imagini noi (variatii via Nano Banana Pro, pornind de la
randarile tale) e Modulul 2, momentan folosim direct imaginea urcata.
"""
import itertools
import os
from datetime import date, timedelta
from pathlib import Path

import content_calendar as cal
import google_drive as gdrive
import caption_generator as captions
import instagram_publisher as ig

POSTING_INTERVAL_DAYS = 2

RAW_GITHUB_BASE = os.environ.get(
      "RAW_GITHUB_BASE",
      "https://raw.githubusercontent.com/USERNAME/REPO/main",
)


def _next_available_slot() -> str:
      data = cal._load_raw()
      used_dates = {e["scheduled_date"] for e in data["entries"] if e["status"] != "failed"}

    candidate = date.today()
    while candidate.isoformat() in used_dates:
              candidate += timedelta(days=POSTING_INTERVAL_DAYS)
          return candidate.isoformat()


def step_1_ingest_new_images():
      print("-> Verific Google Drive pentru randari noi...")
      already_used = cal.already_used_image_ids()
      new_images = gdrive.list_new_images(already_used)

    if not new_images:
              print("  Nicio imagine noua.")
              return

    pillar_cycle = itertools.cycle(cal.CONTENT_PILLARS)

    for img in new_images:
              slot = _next_available_slot()
              pillar = next(pillar_cycle)
              entry = cal.add_entry(
                  source_image_id=img["id"],
                  source_image_name=img["name"],
                  pillar=pillar,
                  scheduled_date=slot,
              )
              print(f"  + Adaugat in calendar: {img['name']} -> {slot} ({pillar})")


def step_2_generate_captions():
      print("-> Generez caption-uri pentru intrarile in asteptare...")
      pending = cal.get_pending_entries()

    for entry in pending:
              try:
                            local_path = gdrive.download_image(
                                              entry["source_image_id"], entry["source_image_name"]
                            )
                            image_description = (
                                f"Randare/proiect de design interior: {entry['source_image_name']}"
                            )
                            caption = captions.generate_caption(entry["pillar"], image_description)

                  cal.update_entry(
                                    entry["id"],
                                    status="ready",
                                    caption=caption,
                                    generated_image_path=str(local_path),
                  )
            print(f"  OK caption generat pentru {entry['source_image_name']}")
except Exception as e:
            cal.mark_failed(entry["id"], str(e))
            print(f"  EROARE la {entry['source_image_name']}: {e}")


def step_3_publish_due_posts():
      print("-> Verific postarile programate pentru azi...")
    due = cal.get_entries_due_today()
    ready_due = [e for e in due if e["status"] == "ready"]

    if not ready_due:
              print("  Nimic de postat azi.")
        return

    for entry in ready_due:
              try:
                            image_filename = Path(entry["generated_image_path"]).name
                            image_url = f"{RAW_GITHUB_BASE}/data/incoming/{image_filename}"

            media_id = ig.publish_image_post(image_url, entry["caption"])
            cal.mark_posted(entry["id"], media_id)
            print(f"  OK postat: {entry['source_image_name']} (media_id={media_id})")
except Exception as e:
            cal.mark_failed(entry["id"], str(e))
            print(f"  EROARE la postare {entry['source_image_name']}: {e}")


if __name__ == "__main__":
      step_1_ingest_new_images()
    step_2_generate_captions()
    step_3_publish_due_posts()
