def _list_item_text(item):
    if isinstance(item, str):
        return item
    text = getattr(item, "text", "")
    children = getattr(item, "children", []) or []
    return text + " " + " ".join(_list_item_text(child) for child in children)


def select_output_format(document):
    """Choose XLSX for predominantly tabular/matrix content, DOCX otherwise."""
    table_score = 0
    narrative_score = 0
    profile_score = 0

    for element in document.elements:
        if element.type in ("table", "structured_data"):
            width = len(element.headers) or (
                len(element.rows[0]) if element.rows else 0
            )
            table_score += width * len(element.rows)

        elif element.type == "profile":
            profile_score += len(element.fields)

        elif element.type in ("paragraph", "heading", "code_block"):
            narrative_score += len(element.text or element.title or "")

        elif element.type == "list":
            narrative_score += sum(len(_list_item_text(item)) for item in element.items)

    structured_score = table_score + profile_score * 2

    if table_score >= 8 and (
        not narrative_score or structured_score >= narrative_score / 20
    ):
        return "xlsx"

    return "docx"
