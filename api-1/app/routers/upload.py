import io
import logging
import uuid

import PyPDF2
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.ai.tools.vision import IMAGE_EXTENSIONS, describe_image_bytes, user_upload_dir
from app.core import config
from app.core.deps import CurrentUser, get_current_user
from app.db.vector_store import add_to_memory

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Upload"])

IMAGE_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


def _extract_pdf(data: bytes) -> str:
    reader = PyPDF2.PdfReader(io.BytesIO(data))
    # extract_text() returns None for image-only pages
    return "\n".join((page.extract_text() or "") for page in reader.pages)


async def _read_limited(file: UploadFile) -> bytes:
    limit = config.MAX_UPLOAD_MB * 1024 * 1024
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(status_code=413, detail=f"File is larger than {config.MAX_UPLOAD_MB} MB.")
    return data


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), user: CurrentUser = Depends(get_current_user)):
    """Parses a PDF or image and stores its content in the caller's long-term memory."""
    name = file.filename or "upload"
    ext = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext != ".pdf" and ext not in IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF and Image files (PNG, JPG, WEBP) are supported.")

    data = await _read_limited(file)
    stored_name = None
    try:
        if ext == ".pdf":
            text = await run_in_threadpool(_extract_pdf, data)
        else:
            # Keep the image so the vision agent can look at it again later
            folder = user_upload_dir(user.id)
            folder.mkdir(parents=True, exist_ok=True)
            stored_name = f"{uuid.uuid4().hex}{ext}"
            (folder / stored_name).write_bytes(data)
            text = await run_in_threadpool(
                describe_image_bytes, data, IMAGE_MIME[ext],
                "Extract and summarize the text and visual content of this image.",
            )
    except Exception as e:
        logger.exception("Upload parsing failed")
        raise HTTPException(status_code=422, detail=f"Could not read the file: {e}")

    if not (text or "").strip():
        raise HTTPException(status_code=400, detail="No readable text/content found in the file.")

    metadata = {"source": name}
    if stored_name:
        metadata["stored_file"] = stored_name
    try:
        await run_in_threadpool(add_to_memory, text, user.id, metadata)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"File was read but could not be saved to memory: {e}")

    return {
        "status": "success",
        "message": f"File '{name}' processed and saved to memory!",
        "content_length": len(text),
        "stored_file": stored_name,
    }
