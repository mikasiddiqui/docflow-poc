from __future__ import annotations

from typing import Any


def map_to_structured_schema(raw_extraction: dict[str, Any]) -> dict[str, Any]:
    extracted_items: list[dict[str, Any]] = []

    for page in raw_extraction.get("pages", []):
        page_number = page.get("page")
        page_text = (page.get("text") or "").strip()

        if page_text:
            extracted_items.append(
                {
                    "page": page_number,
                    "type": "text",
                    "content": page_text,
                    "author": "",
                    "subject": "",
                }
            )

        for annotation in page.get("annotations", []):
            content = (annotation.get("content") or "").strip()
            if not content:
                continue

            extracted_items.append(
                {
                    "page": page_number,
                    "type": "markup" if annotation.get("kind") == "markup" else "annotation",
                    "content": content,
                    "author": annotation.get("author", ""),
                    "subject": annotation.get("subject", ""),
                }
            )

    return {
        "source_file_name": raw_extraction.get("source_file_name", ""),
        "extracted_items": extracted_items,
    }
