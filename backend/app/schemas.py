from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator


class ListItem(BaseModel):
    text: str
    children: list["ListItem"] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_item(cls, value: Any):
        if isinstance(value, str):
            return {"text": value}
        if isinstance(value, dict):
            data = dict(value)
            if "text" not in data:
                for key in ("item", "content", "label", "value"):
                    if isinstance(data.get(key), str):
                        data["text"] = data[key]
                        break
            return data
        return {"text": str(value)}


class ProfileField(BaseModel):
    key: str
    value: str | int | float | None = None


class DocumentElement(BaseModel):
    type: Literal[
        "heading", "paragraph", "table", "profile", "list",
        "code_block", "structured_data"
    ]
    title: str | None = None
    text: str | None = None
    items: list[ListItem] = Field(default_factory=list)
    headers: list[str] = Field(default_factory=list)
    rows: list[list[str | int | float | None]] = Field(default_factory=list)
    has_header: bool = False
    fields: list[ProfileField] = Field(default_factory=list)
    page_number: int = 1
    confidence: float | None = None
    needs_review: bool = False

    @model_validator(mode="before")
    @classmethod
    def normalize_element(cls, value: Any):
        if not isinstance(value, dict):
            return value
        data = dict(value)

        content = data.get("content")
        if isinstance(content, dict):
            for key, val in content.items():
                data.setdefault(key, val)

        aliases = {
            "code": "code_block",
            "preformatted": "code_block",
            "matrix": "structured_data",
            "numeric_matrix": "structured_data",
        }
        if data.get("type") in aliases:
            data["type"] = aliases[data["type"]]

        if data.get("type") in ("table", "structured_data"):
            raw_rows = data.get("rows", [])
            if isinstance(raw_rows, list):
                data["rows"] = [
                    [row] if isinstance(row, str)
                    else row if isinstance(row, list)
                    else [str(row)]
                    for row in raw_rows
                ]
            if "has_header" not in data:
                data["has_header"] = bool(data.get("headers"))

        return data

    @model_validator(mode="after")
    def validate_content(self):
        if self.type in ("table", "structured_data"):
            width = len(self.headers) if self.has_header and self.headers else (
                len(self.rows[0]) if self.rows else 0
            )
            for row in self.rows:
                if width and len(row) != width:
                    raise ValueError("Table row has an incorrect number of cells.")
        if self.type == "profile" and not self.fields:
            raise ValueError("A profile must contain at least one field.")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1.")
        return self


class ExtractedDocument(BaseModel):
    title: str | None = None
    elements: list[DocumentElement] = Field(default_factory=list)
    recommended_format: Literal["docx", "xlsx"] | None = None
    extraction_notes: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_document(cls, value: Any):
        if isinstance(value, dict):
            data = dict(value)
            if "title" not in data and "document_title" in data:
                data["title"] = data.pop("document_title")
            return data
        return value
