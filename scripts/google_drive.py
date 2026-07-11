"""
Integrare Google Drive: preia randari pentru 3 tipuri de continut:
- imagini direct in folderul principal -> postari simple
- subfoldere in "carusele/" -> fiecare subfolder e un carusel (2-10 imagini)
- imagini in "stories/" -> postate ca Instagram Stories

Setup necesar (vezi README.md): Service Account cu acces Viewer la folder.
"""
import os
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
INCOMING_DIR = Path(__file__).parent.parent / "data" / "incoming"

IMAGE_MIME_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/heic",
}
FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"


def _get_service():
    creds_path = os.environ["GDRIVE_SERVICE_ACCOUNT_FILE"]
    creds = service_account.Credentials.from_service_account_file(
        creds_path, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)


def _root_folder_id() -> str:
    return os.environ["GDRIVE_FOLDER_ID"]


def _find_subfolder_id(parent_id: str, name: str) -> str | None:
    """Cauta un subfolder dupa nume in interiorul unui folder parinte."""
    service = _get_service()
    query = (
        f"'{parent_id}' in parents and trashed = false "
        f"and mimeType = '{FOLDER_MIME_TYPE}' and name = '{name}'"
    )
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    return files[0]["id"] if files else None


def list_subfolders(parent_id: str) -> list[dict]:
    """Lista subfolderelor directe dintr-un folder (ex: fiecare carusel)."""
    service = _get_service()
    query = f"'{parent_id}' in parents and trashed = false and mimeType = '{FOLDER_MIME_TYPE}'"
    results = service.files().list(
        q=query, fields="files(id, name)", orderBy="createdTime"
    ).execute()
    return results.get("files", [])


def list_images_in_folder(folder_id: str) -> list[dict]:
    """Lista imaginilor directe dintr-un folder (nu recursiv)."""
    service = _get_service()
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(
        q=query,
        fields="files(id, name, mimeType, createdTime)",
        orderBy="createdTime",
        pageSize=50,
    ).execute()
    files = results.get("files", [])
    return [f for f in files if f["mimeType"] in IMAGE_MIME_TYPES]


def list_new_single_images(already_seen_ids: set[str]) -> list[dict]:
    """Imagini din folderul principal (nu din subfoldere) -> postari simple."""
    images = list_images_in_folder(_root_folder_id())
    return [f for f in images if f["id"] not in already_seen_ids]


def list_new_carousel_folders(already_used_folder_ids: set[str]) -> list[dict]:
    """Subfoldere noi din "carusele/", cu minim 2 imagini fiecare.
    Fiecare rezultat contine: id, name, images (lista de fisiere)."""
    carusele_id = _find_subfolder_id(_root_folder_id(), "carusele")
    if not carusele_id:
        return []

    new_folders = []
    for folder in list_subfolders(carusele_id):
        if folder["id"] in already_used_folder_ids:
            continue
        images = list_images_in_folder(folder["id"])
        if len(images) >= 2:
            new_folders.append({
                "id": folder["id"],
                "name": folder["name"],
                "images": images[:10],
            })
    return new_folders


def list_new_story_images(already_seen_ids: set[str]) -> list[dict]:
    """Imagini noi din "stories/" -> postate ca Instagram Stories."""
    stories_id = _find_subfolder_id(_root_folder_id(), "stories")
    if not stories_id:
        return []
    images = list_images_in_folder(stories_id)
    return [f for f in images if f["id"] not in already_seen_ids]


def download_image(file_id: str, file_name: str) -> Path:
    service = _get_service()
    INCOMING_DIR.mkdir(parents=True, exist_ok=True)
    local_path = INCOMING_DIR / file_name

    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(local_path, "wb")
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()

    return local_path
