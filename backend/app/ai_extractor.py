import os
from pathlib import Path

from app.schemas import ExtractedDocument
from app.region_extractor import extract_regions
from app.providers.extraction_manager import extract_with_fallback


def _extract_full_image(image_path: str) -> ExtractedDocument:
    prompt = """
Extract this document image into compact JSON only:
{
  "title": null,
  "elements": [
    {"type":"heading","text":"..."},
    {"type":"paragraph","text":"..."},
    {"type":"list","items":["..."]},
    {"type":"table","title":null,"headers":[],"has_header":false,
     "rows":[["..."]]},
    {"type":"profile","fields":[{"key":"...","value":"..."}]},
    {"type":"code_block","text":"..."},
    {"type":"structured_data","rows":[["..."]]}
  ],
  "recommended_format": null,
  "extraction_notes": []
}
Preserve all visible text, numbers, symbols and reading order. Do not invent values.
Nested list items may be {"text":"...","children":[...]}. Tables may have no
headers. Every table row must be an array of cells. Return JSON only.
"""
    import json
    import re

    raw = extract_with_fallback(str(image_path), prompt)
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    data = json.loads(cleaned)
    return ExtractedDocument.model_validate(data)


def extract_document(image_path: str) -> ExtractedDocument:
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(path)

    enabled = os.getenv("REGION_EXTRACTION_ENABLED", "true").lower() in {
        "1", "true", "yes", "on"
    }

    if enabled:
        return extract_regions(str(path))

    return _extract_full_image(str(path))
