def validate_document(document):
    warnings = []

    if not document.elements:
        warnings.append("No content extracted.")
        return warnings

    for index, element in enumerate(document.elements):
        label = f"Element {index + 1}"

        if element.needs_review:
            warnings.append(f"{label} needs review.")

        if element.confidence is not None and element.confidence < 0.75:
            warnings.append(f"{label} has low confidence.")

        if element.type in ("table", "structured_data"):
            if not element.rows:
                warnings.append(f"{label} contains no data rows.")
                continue

            expected_width = len(element.headers) or len(element.rows[0])
            for row_index, row in enumerate(element.rows):
                if len(row) != expected_width:
                    warnings.append(
                        f"{label}, row {row_index + 1} has "
                        f"{len(row)} cells; expected {expected_width}."
                    )

    return warnings
