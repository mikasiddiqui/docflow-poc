from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import fitz


MARKUP_SUBTYPES = {"Highlight", "Underline", "StrikeOut", "Squiggly"}


def extract_pdf_content(pdf_path: Path, logger: logging.Logger | None = None) -> dict[str, Any]:
    logger = logger or logging.getLogger(__name__)
    extraction_notes: list[str] = []
    pages: list[dict[str, Any]] = []
    annotation_count = 0
    markup_count = 0

    with fitz.open(pdf_path) as document:
        for page_index in range(document.page_count):
            page = document.load_page(page_index)
            page_text = page.get_text("text").strip()
            annotations = _extract_annotations(page, logger)
            annotation_count += len(annotations)
            markup_count += sum(1 for item in annotations if item["kind"] == "markup")

            pages.append(
                {
                    "page": page_index + 1,
                    "text": page_text,
                    "annotations": annotations,
                }
            )

    if annotation_count == 0:
        note = "No machine-readable annotations found; plain text extraction is being used as the main fallback."
        extraction_notes.append(note)
        logger.info(note)

    return {
        "source_file_name": pdf_path.name,
        "page_count": len(pages),
        "annotation_count": annotation_count,
        "markup_count": markup_count,
        "extraction_notes": extraction_notes,
        "pages": pages,
    }


def _extract_annotations(page: fitz.Page, logger: logging.Logger) -> list[dict[str, Any]]:
    extracted_annotations: list[dict[str, Any]] = []
    annotations_iter = page.annots()

    if annotations_iter is None:
        return extracted_annotations

    for annotation in annotations_iter:
        try:
            annotation_type = annotation.type[1] or "Unknown"
            kind = "markup" if annotation_type in MARKUP_SUBTYPES else "annotation"
            info = annotation.info or {}
            content = (info.get("content") or "").strip()

            # Markup annotations often carry the useful text in the bounding box
            # rather than in the annotation's explicit content field.
            if not content:
                content = _extract_text_from_annotation_bounds(page, annotation)

            extracted_annotations.append(
                {
                    "subtype": annotation_type,
                    "kind": kind,
                    "content": content,
                    "author": (info.get("title") or "").strip(),
                    "subject": (info.get("subject") or "").strip(),
                    "created_at": (info.get("creationDate") or "").strip(),
                    "modified_at": (info.get("modDate") or "").strip(),
                    "rect": _rect_to_list(annotation.rect),
                }
            )
        except Exception as exc:  # pragma: no cover - defensive POC guardrail
            logger.warning("Skipping unreadable annotation on page %s: %s", page.number + 1, exc)

    return extracted_annotations


def _extract_text_from_annotation_bounds(page: fitz.Page, annotation: fitz.Annot) -> str:
    if annotation.rect.is_empty:
        return ""
    return page.get_textbox(annotation.rect).strip()


def _rect_to_list(rect: fitz.Rect) -> list[float]:
    return [round(rect.x0, 2), round(rect.y0, 2), round(rect.x1, 2), round(rect.y1, 2)]
