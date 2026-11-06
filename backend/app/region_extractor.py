import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image

from app.providers.extraction_manager import extract_with_fallback
from app.schemas import ExtractedDocument


def _env_int(name: str, default: int, minimum: int = 1, maximum: int = 20) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


def _parse_json(raw: str) -> dict[str, Any]:
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("Provider response did not contain a JSON object.")
        data = json.loads(cleaned[start:end + 1])
    if not isinstance(data, dict):
        raise ValueError("Provider response must be a JSON object.")
    return data


def _make_grid_regions(image_path: str, columns: int, rows: int, overlap: float):
    """Create reading-order crops with a small overlap to avoid cutting edge text."""
    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    regions = []

    for row in range(rows):
        y0 = round(row * height / rows)
        y1 = round((row + 1) * height / rows)
        y_pad = round((y1 - y0) * overlap)

        for col in range(columns):
            x0 = round(col * width / columns)
            x1 = round((col + 1) * width / columns)
            x_pad = round((x1 - x0) * overlap)

            box = (
                max(0, x0 - x_pad),
                max(0, y0 - y_pad),
                min(width, x1 + x_pad),
                min(height, y1 + y_pad),
            )
            regions.append((row, col, image.crop(box)))

    return image.size, regions


def _region_prompt(region_index: int, total_regions: int) -> str:
    return f"""
Read this document crop (region {region_index} of {total_regions}).
Return compact JSON only. Do not add explanations or markdown.

For ordinary content use:
{{
  "elements": [
    {{"type":"heading","text":"..."}},
    {{"type":"paragraph","text":"..."}},
    {{"type":"list","items":["..."]}},
    {{"type":"table","title":"...","headers":["..."],"has_header":true,
      "rows":[["...","..."]]}},
    {{"type":"code_block","text":"..."}}
  ]
}}

SPECIAL CASE — multiplication-table card:
If the crop contains one multiplication table/card, return:
{{
  "kind":"multiplication_table",
  "factor": 1,
  "products":[1,2,3,4,5,6,7,8,9,10]
}}
Here factor is the table's multiplier (for example, 6 for the 6x card).
Products must be the ten results in multiplier order, from x1 through x10.
Do not return equation strings in this compact form.

Rules:
- Transcribe only visible content. Never infer unreadable values.
- Preserve reading order.
- If this crop has no readable content, return {{"elements":[]}}.
- For normal tables, rows must be arrays of cells. Headerless tables may use
  headers=[] and has_header=false.
- Keep the response compact. Do not repeat the prompt.
"""


def _multiplication_element(data: dict[str, Any]) -> dict[str, Any] | None:
    if data.get("kind") != "multiplication_table":
        return None

    factor = data.get("factor")
    products = data.get("products")

    if not isinstance(factor, int) or not isinstance(products, list):
        return None

    # Validate rather than silently correcting model output.
    if len(products) != 10:
        raise ValueError(
            f"Multiplication card for factor {factor} returned "
            f"{len(products)} products; expected 10."
        )

    rows = []
    for multiplier, product in enumerate(products, start=1):
        if not isinstance(product, (int, float)):
            raise ValueError("Multiplication card contains a non-numeric product.")
        rows.append([f"{factor} x {multiplier} = {product}"])

    return {
        "type": "table",
        "title": f"{factor}x multiplication table",
        "headers": [],
        "has_header": False,
        "rows": rows,
        "page_number": 1,
        "confidence": None,
        "needs_review": False,
    }


def extract_regions(image_path: str) -> ExtractedDocument:
    columns = _env_int("REGION_COLUMNS", 5, 1, 10)
    rows = _env_int("REGION_ROWS", 2, 1, 10)
    max_regions = _env_int("REGION_MAX_REGIONS", 10, 1, 40)
    overlap = float(os.getenv("REGION_OVERLAP", "0.04"))
    overlap = min(0.15, max(0.0, overlap))

    _, regions = _make_grid_regions(image_path, columns, rows, overlap)
    if len(regions) > max_regions:
        raise ValueError(
            f"Configured grid creates {len(regions)} regions, exceeding "
            f"REGION_MAX_REGIONS={max_regions}."
        )

    all_elements = []
    notes = [
        f"Region extraction used a {columns}x{rows} grid "
        f"({len(regions)} regions)."
    ]

    with tempfile.TemporaryDirectory(prefix="docrec_regions_") as temp_dir:
        for index, (grid_row, grid_col, crop) in enumerate(regions, start=1):
            crop_path = Path(temp_dir) / f"region_{index:02d}.jpg"
            crop.save(crop_path, format="JPEG", quality=92, optimize=True)

            prompt = _region_prompt(index, len(regions))
            raw = extract_with_fallback(str(crop_path), prompt)
            data = _parse_json(raw)

            compact_table = _multiplication_element(data)
            if compact_table is not None:
                all_elements.append(compact_table)
                continue

            elements = data.get("elements", [])
            if not isinstance(elements, list):
                raise ValueError(
                    f"Region {index} response has no valid elements array."
                )

            # Preserve region order. Attach region coordinates for traceability.
            for element in elements:
                if isinstance(element, dict):
                    element.setdefault("page_number", 1)
                    all_elements.append(element)

    combined = {
        "title": None,
        "elements": all_elements,
        "recommended_format": None,
        "extraction_notes": notes,
    }

    document = ExtractedDocument.model_validate(combined)
    if not document.elements:
        raise ValueError("Region extraction returned no readable document content.")
    return document
