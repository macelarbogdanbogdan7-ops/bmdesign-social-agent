"""
Genereaza variatii de marketing pornind de la o randare existenta, folosind
Nano Banana Pro (google/gemini-3-pro-image-preview) prin OpenRouter.

Urmeaza abordarea ta consacrata: "gradeaza" fotografia existenta, NU o
redeseneaza. Toate culorile, materialele si texturile raman blocate (lock),
iar instructiunile negative previn modificari nedorite ale designului.
"""
import base64
import os
from pathlib import Path

import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-3-pro-image-preview"

GENERATED_DIR = Path(__file__).parent.parent / "data" / "generated"

# Prompt de baza: grading, nu redesign. Ajusteaza variatiile in VARIATION_ANGLES.
BASE_PROMPT = """You are grading an existing interior design photograph for social \
media marketing. This is NOT a redesign task - you are adjusting composition, \
crop, lighting mood, or camera angle ONLY, as if a photographer reframed the \
same shot.

STRICT LOCKS (do not change under any circumstance):
- All surface colors, finishes, and material textures exactly as shown
- All furniture, fixtures, and their exact positions
- All architectural elements (walls, ceiling, windows, cabinetry layout)

Variation requested: {variation_instruction}

Negative constraints: do NOT redesign, do NOT change colors, do NOT add or \
remove objects, do NOT change materials, do NOT alter proportions."""

VARIATION_ANGLES = {
    "feed_square": "Recompose as a tight 1:1 square crop emphasizing the main "
                   "focal point (island/counter), balanced for an Instagram feed post.",
    "story_vertical": "Recompose as a 9:16 vertical crop suitable for Instagram "
                       "Stories, keeping the most visually striking element centered.",
    "warm_mood": "Keep the exact same framing, but grade the lighting slightly "
                 "warmer and softer, as if shot during golden hour, without "
                 "changing any material colors.",
}


def _encode_image(image_path: Path) -> str:
    data = image_path.read_bytes()
    b64 = base64.b64encode(data).decode("utf-8")
    ext = image_path.suffix.lstrip(".").lower()
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext
    return f"data:image/{mime};base64,{b64}"


def generate_variation(source_image_path: Path, variation_key: str) -> Path:
    """Genereaza o variatie a imaginii sursa si o salveaza in data/generated/.
    Returneaza path-ul local al imaginii generate."""
    variation_instruction = VARIATION_ANGLES.get(
        variation_key, VARIATION_ANGLES["feed_square"]
    )
    prompt = BASE_PROMPT.format(variation_instruction=variation_instruction)

    image_data_url = _encode_image(source_image_path)

    response = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_data_url}},
                    ],
                }
            ],
            "modalities": ["image", "text"],
        },
        timeout=120,
    )
    response.raise_for_status()
    result = response.json()

    images = result["choices"][0]["message"].get("images", [])
    if not images:
        raise RuntimeError(f"Niciun rezultat imagine de la {MODEL}: {result}")

    image_url = images[0]["image_url"]["url"]
    if image_url.startswith("data:"):
        header, b64_data = image_url.split(",", 1)
        img_bytes = base64.b64decode(b64_data)
    else:
        img_bytes = requests.get(image_url, timeout=60).content

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    out_name = f"{source_image_path.stem}_{variation_key}.png"
    out_path = GENERATED_DIR / out_name
    out_path.write_bytes(img_bytes)

    return out_path
