
from pathlib import Path

from app.ai_extractor import extract_document


# Change this to the image you want to test.
image_path = Path("./test_images/sample2.jpg")


if not image_path.exists():
    raise FileNotFoundError(
        f"Test image not found: {image_path.resolve()}"
    )


print("Testing document extraction...")

document = extract_document(image_path)

print("\n========== EXTRACTION RESULT ==========")

print("Document title:", document.title)

print("Recommended format:", document.recommended_format)

print("Number of elements:", len(document.elements))

print("\nExtraction notes:")

for note in document.extraction_notes:
    print("-", note)

print("\n========== EXTRACTED ELEMENTS ==========")

for index, element in enumerate(document.elements, start=1):

    print(f"\nElement {index}")
    print("Type:", element.type)
    print("Title:", element.title)
    print("Confidence:", element.confidence)
    print("Needs review:", element.needs_review)

    if element.type in ("heading", "paragraph"):
        print("Text:", element.text)

    elif element.type == "table":
        print("Headers:", element.headers)
        print("Rows:", element.rows)

    elif element.type == "profile":
        for field in element.fields:
            print(f"{field.key}: {field.value}")

    elif element.type == "list":
        for item in element.items:
            print("-", item)

print("\nExtraction test completed successfully.")
