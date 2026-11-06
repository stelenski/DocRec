from pathlib import Path
from docx import Document
from docx.shared import Pt


def _add_list_items(doc, items, level=0):
    for item in items:
        text = item.text if hasattr(item, "text") else str(item)
        paragraph = doc.add_paragraph(style="List Bullet" if level == 0 else "List Bullet 2")
        paragraph.paragraph_format.left_indent = Pt(18 * level)
        paragraph.add_run(text)
        children = getattr(item, "children", []) if not isinstance(item, str) else []
        if children:
            _add_list_items(doc, children, level + 1)


def _add_grid_table(doc, headers, rows, has_header=True):
    width = len(headers) if headers else (len(rows[0]) if rows else 0)
    if width == 0:
        return

    table = doc.add_table(rows=0, cols=width)
    table.style = "Light Shading Accent 1"

    if headers and has_header:
        cells = table.add_row().cells
        for cell, value in zip(cells, headers):
            cell.text = "" if value is None else str(value)

    for row in rows:
        cells = table.add_row().cells
        for cell, value in zip(cells, row):
            cell.text = "" if value is None else str(value)


def generate_word(document, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = Document()
    if document.title:
        doc.add_heading(document.title, level=0)

    for element in document.elements:
        if element.type == "heading":
            doc.add_heading(element.text or element.title or "", level=1)

        elif element.type == "paragraph":
            doc.add_paragraph(element.text or "")

        elif element.type == "list":
            if element.title:
                doc.add_heading(element.title, level=2)
            _add_list_items(doc, element.items)

        elif element.type == "profile":
            if element.title:
                doc.add_heading(element.title, level=2)
            table = doc.add_table(rows=0, cols=2)
            table.style = "Light Shading Accent 1"
            for field in element.fields:
                cells = table.add_row().cells
                cells[0].text = field.key
                cells[1].text = "" if field.value is None else str(field.value)

        elif element.type == "table":
            if element.title:
                doc.add_heading(element.title, level=2)
            _add_grid_table(
                doc, element.headers, element.rows,
                has_header=element.has_header
            )

        elif element.type == "structured_data":
            if element.title:
                doc.add_heading(element.title, level=2)
            _add_grid_table(doc, element.headers, element.rows,
                            has_header=element.has_header)

        elif element.type == "code_block":
            if element.title:
                doc.add_heading(element.title, level=2)
            paragraph = doc.add_paragraph()
            run = paragraph.add_run(element.text or "")
            run.font.name = "Consolas"
            run.font.size = Pt(9)

    doc.save(output_path)
    return output_path
