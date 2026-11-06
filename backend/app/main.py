import time
from pathlib import Path

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    Form
)

from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .ai_extractor import extract_document
from .classifier import select_output_format
from .validator import validate_document

from .word_generator import generate_word
from .excel_generator import generate_excel

from .file_manager import (
    save_uploaded_file,
    get_output_path
)


app = FastAPI(
    title="Document Reconstruction API",
    version="1.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"]
)


# Temporary job storage for MVP
JOBS = {}


@app.get("/api/health")
def health():

    return {
        "status": "running"
    }


@app.post("/api/analyze")
async def analyze_document(
    file: UploadFile = File(...)
):

    allowed_types = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp"
    }

    if file.content_type not in allowed_types:

        raise HTTPException(
            status_code=415,
            detail="Unsupported file format."
        )

    content = await file.read()

    if len(content) > 15 * 1024 * 1024:

        raise HTTPException(
            status_code=413,
            detail="File too large."
        )

    job_id, image_path = save_uploaded_file(
        content,
        allowed_types[file.content_type]
    )

    start_time = time.perf_counter()

    try:

        # 1. AI extraction
        document = extract_document(image_path)

        # 2. Output selection
        recommended_format = select_output_format(
            document
        )

        # 3. Validation
        warnings = validate_document(
            document
        )

        # 4. Store the extracted document
        JOBS[job_id] = {
            "document": document,
            "format": recommended_format
        }

        elapsed = time.perf_counter() - start_time

        return {
            "job_id": job_id,

            "title": document.title,

            "elements": [
                element.model_dump()
                for element in document.elements
            ],

            "recommended_format": recommended_format,

            "model_recommendation": (
                document.recommended_format
            ),

            "warnings": warnings,

            "extraction_notes": document.extraction_notes,

            "processing_time": round(elapsed, 2)
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(error)}"
        )


@app.post("/api/generate/{job_id}")
def generate_document(
    job_id: str,
    output_format: str = Form(...)
):

    if job_id not in JOBS:

        raise HTTPException(
            status_code=404,
            detail="Document job not found."
        )

    if output_format not in ["docx", "xlsx"]:

        raise HTTPException(
            status_code=400,
            detail="Invalid output format."
        )

    document = JOBS[job_id]["document"]

    output_path = get_output_path(
        job_id,
        output_format
    )

    if output_format == "docx":

        generate_word(
            document,
            output_path
        )

    else:

        generate_excel(
            document,
            output_path
        )

    return {
        "job_id": job_id,
        "filename": output_path.name,
        "download_url": f"/api/download/{job_id}/{output_format}"
    }


@app.get("/api/download/{job_id}/{extension}")
def download_document(
    job_id: str,
    extension: str
):

    if extension not in ["docx", "xlsx"]:

        raise HTTPException(
            status_code=400,
            detail="Invalid file extension."
        )

    output_path = get_output_path(
        job_id,
        extension
    )

    if not output_path.exists():

        raise HTTPException(
            status_code=404,
            detail="Generated file not found."
        )

    media_types = {
        "docx": (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),

        "xlsx": (
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    }

    return FileResponse(
        output_path,
        filename=f"reconstructed_document.{extension}",
        media_type=media_types[extension]
    )