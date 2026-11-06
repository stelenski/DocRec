import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter()

UPLOAD_DIR = Path("storage/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png"
}

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format"
        )

    file_data = await file.read()

    if not file_data or len(file_data) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="Empty file or file exceeds 10 MB limit"
        )

    job_id = str(uuid.uuid4())

    extension = ALLOWED_TYPES[file.content_type]

    file_path = UPLOAD_DIR / f"{job_id}{extension}"

    file_path.write_bytes(file_data)

    return {
        "job_id": job_id,
        "filename": file.filename,
        "status": "uploaded"
    }