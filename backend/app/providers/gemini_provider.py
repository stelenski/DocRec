
import json
import mimetypes

from pathlib import Path

from google import genai
from google.genai import types

from app.config import settings
from app.schemas import ExtractedDocument


EXTRACTION_PROMPT = """
You are an expert document understanding and information extraction system.

Analyze the supplied document image.

Extract ALL meaningful content and classify each region into one
of the following categories:

1. heading
2. paragraph
3. table
4. profile
5. list

EXTRACTION RULES:

- Preserve the original text accurately.
- Do not invent missing information.
- Preserve table headers and all rows.
- Keep separate tables as separate elements.
- Do not classify a table as a paragraph.
- A profile contains key-value pairs.
- Preserve the reading order of elements.
- Do not omit explanatory text surrounding tables.
- Use null for unreadable values where appropriate.
- Set needs_review to true for uncertain elements.
- Assign confidence between 0 and 1.

Return ONLY valid JSON.

Use this structure:

{
    "title": "Document title",
    "recommended_format": "xlsx",
    "extraction_notes": [],
    "elements": [
        {
            "type": "heading",
            "title": null,
            "text": "Heading text",
            "items": [],
            "headers": [],
            "rows": [],
            "fields": [],
            "page_number": 1,
            "confidence": 0.98,
            "needs_review": false
        },
        {
            "type": "paragraph",
            "title": null,
            "text": "Paragraph text",
            "items": [],
            "headers": [],
            "rows": [],
            "fields": [],
            "page_number": 1,
            "confidence": 0.98,
            "needs_review": false
        },
        {
            "type": "table",
            "title": "Table title",
            "text": null,
            "items": [],
            "headers": ["Column 1", "Column 2"],
            "rows": [["Value 1", "Value 2"]],
            "fields": [],
            "page_number": 1,
            "confidence": 0.95,
            "needs_review": false
        },
        {
            "type": "profile",
            "title": "Profile title",
            "text": null,
            "items": [],
            "headers": [],
            "rows": [],
            "fields": [
                {"key": "Name", "value": "Example"}
            ],
            "page_number": 1,
            "confidence": 0.98,
            "needs_review": false
        },
        {
            "type": "list",
            "title": null,
            "text": null,
            "items": ["Item 1", "Item 2"],
            "headers": [],
            "rows": [],
            "fields": [],
            "page_number": 1,
            "confidence": 0.98,
            "needs_review": false
        }
    ]
}

Choose "xlsx" for predominantly tabular or structured information.

Choose "docx" for predominantly narrative information.

Return no Markdown code fences or explanations.
"""


def extract_with_gemini(image_path: str | Path) -> ExtractedDocument:

    if not settings.GEMINI_ENABLED:
        raise RuntimeError("Gemini provider is disabled.")

    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    mime_type, _ = mimetypes.guess_type(
        image_path.name
    )

    if mime_type is None or not mime_type.startswith("image/"):
        raise ValueError(
            f"Unsupported image type: {image_path.name}"
        )

    client = genai.Client(
        api_key=settings.GEMINI_API_KEY
    )

    image_bytes = image_path.read_bytes()

    image_part = types.Part.from_bytes(
        data=image_bytes,
        mime_type=mime_type
    )

    print(
        f"[Gemini] Sending image to {settings.GEMINI_MODEL}"
    )

    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=[
            EXTRACTION_PROMPT,
            image_part
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0
        )
    )

    if not response.text:
        raise ValueError(
            "Gemini returned an empty response."
        )

    try:
        extracted_data = json.loads(response.text)

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Gemini returned invalid JSON: {exc}"
        ) from exc

    document = ExtractedDocument.model_validate(
        extracted_data
    )

    print("[Gemini] Extraction successful.")

    return document
