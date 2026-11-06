from pathlib import Path
import uuid


BASE_DIR = Path("storage")

UPLOAD_DIR = BASE_DIR / "uploads"

OUTPUT_DIR = BASE_DIR / "generated"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def save_uploaded_file(file_bytes, extension):

    job_id = str(uuid.uuid4())

    file_path = UPLOAD_DIR / (
        f"{job_id}{extension}"
    )

    file_path.write_bytes(file_bytes)

    return job_id, file_path


def get_output_path(job_id, extension):

    return OUTPUT_DIR / (
        f"{job_id}.{extension}"
    )