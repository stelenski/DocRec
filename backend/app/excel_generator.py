from pathlib import Path
import re

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter


def clean_sheet_name(name, existing_names):
    name = re.sub(r'[\\/*?:\[\]]', '', str(name or "Sheet")).strip()[:31] or "Sheet"
    original, counter = name, 1
    while name.lower() in {n.lower() for n in existing_names}:
        suffix = f"_{counter}"
        name = original[:31 - len(suffix)] + suffix
        counter += 1
    return name


def _write_grid(ws, start_row, headers, rows, has_header, title=None):
    row = start_row
    if title:
        ws.cell(row=row, column=1, value=title).font = Font(bold=True, size=14)
        row += 2

    width = len(headers) if headers else (len(rows[0]) if rows else 0)
    if width == 0:
        return row

    if headers and has_header:
        for col, value in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=str(value or ""))
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="1F4E78")
            cell.alignment = Alignment(horizontal="center", wrap_text=True)
        row += 1

    data_start = row
    for values in rows:
        for col, value in enumerate(values, 1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
        row += 1

    for col in range(1, width + 1):
        letter = get_column_letter(col)
        candidates = [len(str(ws.cell(r, col).value or "")) for r in range(start_row, row)]
        ws.column_dimensions[letter].width = min(max(max(candidates or [12]) + 2, 12), 42)

    if has_header and headers and row > data_start:
        ws.freeze_panes = f"A{data_start}"
    return row + 1


def _write_list(ws, row, items, level=0):
    for item in items:
        text = item.text if hasattr(item, "text") else str(item)
        cell = ws.cell(row=row, column=1, value=("  " * level) + "• " + text)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        children = getattr(item, "children", []) if not isinstance(item, str) else []
        row += 1
        if children:
            row = _write_list(ws, row, children, level + 1)
    return row


def generate_excel(document, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    ws = wb.active
    ws.title = "Document Content"
    ws.column_dimensions["A"].width = 42
    ws.column_dimensions["B"].width = 42
    ws.column_dimensions["C"].width = 24
    row = 1
    table_count = 0

    if document.title:
        ws.cell(row=row, column=1, value=document.title).font = Font(bold=True, size=16)
        row += 2

    # Preserve source order: tables and narrative elements share one primary sheet.
    # This avoids scattering related fragments across many worksheets.
    for element in document.elements:
        if element.type == "heading":
            text = element.text or element.title or ""
            ws.cell(row=row, column=1, value=text).font = Font(bold=True, size=14)
            row += 2

        elif element.type == "paragraph":
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
            ws.cell(row=row, column=1, value=element.text or "").alignment = Alignment(wrap_text=True, vertical="top")
            row += 2

        elif element.type == "list":
            if element.title:
                ws.cell(row=row, column=1, value=element.title).font = Font(bold=True)
                row += 1
            row = _write_list(ws, row, element.items) + 1

        elif element.type == "profile":
            if element.title:
                ws.cell(row=row, column=1, value=element.title).font = Font(bold=True, size=13)
                row += 1
            for field in element.fields:
                ws.cell(row=row, column=1, value=field.key).font = Font(bold=True)
                ws.cell(row=row, column=2, value=field.value)
                row += 1
            row += 1

        elif element.type in ("table", "structured_data"):
            table_count += 1
            row = _write_grid(
                ws, row, element.headers, element.rows,
                element.has_header, element.title or f"Table {table_count}"
            )

        elif element.type == "code_block":
            if element.title:
                ws.cell(row=row, column=1, value=element.title).font = Font(bold=True)
                row += 1
            cell = ws.cell(row=row, column=1, value=element.text or "")
            cell.font = Font(name="Consolas", size=10)
            cell.alignment = Alignment(wrap_text=False, vertical="top")
            row += max(2, (element.text or "").count("\n") + 2)

    thin = Side(style="thin", color="D9E2F3")
    for sheet in wb.worksheets:
        for cells in sheet.iter_rows():
            for cell in cells:
                if cell.value is not None:
                    cell.border = Border(bottom=thin)

    wb.save(output_path)
    return output_path
