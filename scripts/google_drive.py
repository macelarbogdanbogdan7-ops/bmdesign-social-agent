"""
Verifica folderul de Google Drive pentru randari noi si le descarca local,
in /data/incoming/, ca sa poata fi folosite de restul pipeline-ului.

Setup necesar (vezi README.md):
1. Creezi un Service Account in Google Cloud Console.
2. Activezi Google Drive API pentru proiect.
3. Descarci cheia JSON a Service Account-ului.
4. Partajezi folderul tau de Drive cu adresa de email a Service Account-ului
   (ex: bmdesign-agent@proiect.iam.gserviceaccount.com), cu drept de "Viewer".
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


def _get_service():
    creds_path = os.environ["GDRIVE_SERVICE_ACCOUNT_FILE"]
    creds = service_account.Credentials.from_service_account_file(
        creds_path, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)


def list_new_images(already_seen_ids: set[str]) -> list[dict]:
    service = _get_service()
    folder_id = os.environ["GDRIVE_FOLDER_ID"]

    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(
        q=query,
        fields="files(id, name, mimeType, createdTime)",
        orderBy="createdTime desc",
        pageSize=50,
    ).execute()

    files = results.get("files", [])
    new_images = [
        f for f in files
        if f["mimeType"] in IMAGE_MIME_TYPES and f["id"] not in already_seen_ids
    ]
    return new_images


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
