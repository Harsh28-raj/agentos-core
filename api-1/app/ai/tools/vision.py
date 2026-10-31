import base64
import mimetypes
from pathlib import Path

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.core import config as app_config

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def user_upload_dir(user_id: str) -> Path:
    return (app_config.UPLOAD_DIR / str(user_id)).resolve()


def describe_image_bytes(data: bytes, mime_type: str, prompt: str) -> str:
    """Sends an image to the configured vision-capable Groq model."""
    from app.ai.llm import get_vision_llm

    encoded = base64.b64encode(data).decode("utf-8")
    msg = get_vision_llm().invoke([{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded}"}},
        ],
    }])
    return msg.content


@tool
def analyze_image(
    file_name: str,
    prompt: str = "Extract and summarize the text and visual content of this image.",
    config: RunnableConfig = None,
) -> str:
    """Analyze an image the user uploaded earlier (text, diagrams, receipts, screenshots).

    Args:
        file_name: The stored file name returned by the upload (e.g. '3f2a...c1.png').
        prompt: What to look for in the image.
    """
    user_id = (config or {}).get("configurable", {}).get("user_id")
    if not user_id:
        return "Error: no authenticated user for this request."
    base = user_upload_dir(user_id)
    # Only bare names inside the caller's own upload folder: no paths, no traversal.
    path = (base / Path(file_name).name).resolve()
    if path.parent != base or path.suffix.lower() not in IMAGE_EXTENSIONS:
        return "Error: unknown image. Ask the user to upload the image first."
    if not path.exists():
        uploads = sorted(p.name for p in base.glob("*") if p.suffix.lower() in IMAGE_EXTENSIONS) if base.exists() else []
        return f"Error: image '{path.name}' not found. Uploaded images: {', '.join(uploads) or 'none'}."
    try:
        mime_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
        return describe_image_bytes(path.read_bytes(), mime_type, prompt)
    except Exception as e:
        return f"Error analyzing image: {e}"
