from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import AppSettings
from .docx_generator import generate_docx
from .graph_client import GraphClient
from .mapper import map_to_structured_schema
from .pdf_extractor import extract_pdf_content


def process_document(
    *,
    settings: AppSettings,
    graph_client: GraphClient,
    input_drive_id: str,
    input_file_id: str | None = None,
    input_file_path: str | None = None,
    output_drive_id: str | None = None,
    output_folder_id: str | None = None,
    output_folder_path: str | None = None,
    template_drive_id: str | None = None,
    template_file_id: str | None = None,
    template_file_path: str | None = None,
    local_template_path: str | None = None,
    upload_file_name: str | None = None,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    logger = logger or configure_logging(settings)
    output_dir = settings.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    output_drive_id = output_drive_id or settings.graph.default_output_drive_id or input_drive_id
    template_path, template_source = resolve_template_path(
        graph_client=graph_client,
        output_dir=output_dir,
        input_drive_id=input_drive_id,
        logger=logger,
        template_drive_id=template_drive_id,
        template_file_id=template_file_id,
        template_file_path=template_file_path,
        local_template_path=local_template_path,
    )

    downloaded_pdf_path = output_dir / "downloaded_input.pdf"
    source_metadata = graph_client.download_file(
        input_drive_id,
        downloaded_pdf_path,
        item_id=input_file_id,
        item_path=input_file_path,
    )
    actual_download_path = rename_downloaded_file(downloaded_pdf_path, source_metadata.get("name"))
    logger.info("Downloaded source PDF: %s", actual_download_path.name)

    raw_extraction = extract_pdf_content(actual_download_path, logger=logger)
    raw_extraction_path = output_dir / "raw_extraction.json"
    write_json(raw_extraction_path, raw_extraction)

    structured_content = map_to_structured_schema(raw_extraction)
    structured_content_path = output_dir / "structured_content.json"
    write_json(structured_content_path, structured_content)

    generated_docx_path = output_dir / "generated_report.docx"
    generate_docx(template_path, structured_content, generated_docx_path)
    logger.info("Generated DOCX: %s", generated_docx_path.name)

    upload_name = upload_file_name or f"{actual_download_path.stem}-generated.docx"
    upload_metadata = graph_client.upload_file(
        output_drive_id,
        generated_docx_path,
        upload_name,
        parent_folder_id=output_folder_id,
        parent_folder_path=output_folder_path,
    )
    logger.info("Uploaded DOCX to Microsoft storage as: %s", upload_name)

    audit_payload = build_audit_payload(
        source_metadata=source_metadata,
        raw_extraction=raw_extraction,
        structured_content=structured_content,
        upload_metadata=upload_metadata,
        template_source=template_source,
        inputs={
            "drive_id": input_drive_id,
            "input_file_id": input_file_id,
            "input_file_path": input_file_path,
            "output_drive_id": output_drive_id,
            "output_folder_id": output_folder_id,
            "output_folder_path": output_folder_path,
            "template_drive_id": template_drive_id,
            "template_file_id": template_file_id,
            "template_file_path": template_file_path,
            "local_template_path": str(Path(local_template_path).expanduser().resolve()) if local_template_path else None,
        },
        local_paths={
            "downloaded_pdf": str(actual_download_path),
            "downloaded_template": str(template_path),
            "raw_extraction": str(raw_extraction_path),
            "structured_content": str(structured_content_path),
            "generated_docx": str(generated_docx_path),
        },
    )
    audit_path = output_dir / "run_audit.json"
    write_json(audit_path, audit_payload)

    return {
        "status": "ok",
        "source_file_name": raw_extraction["source_file_name"],
        "extracted_items": len(structured_content["extracted_items"]),
        "uploaded_file_name": upload_name,
        "audit_path": str(audit_path),
        "source_file": source_metadata,
        "uploaded_file": upload_metadata,
    }


def configure_logging(settings: AppSettings, *, logger_name: str = "docflow") -> logging.Logger:
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, settings.log_level, logging.INFO))
    logger.propagate = False

    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        file_handler = logging.FileHandler(settings.output_dir / "run.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def build_audit_payload(
    *,
    source_metadata: dict[str, Any],
    raw_extraction: dict[str, Any],
    structured_content: dict[str, Any],
    upload_metadata: dict[str, Any],
    template_source: dict[str, Any],
    inputs: dict[str, Any],
    local_paths: dict[str, str],
) -> dict[str, Any]:
    return {
        "run_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "inputs": inputs,
        "source_file": {
            "id": source_metadata.get("id"),
            "name": source_metadata.get("name"),
            "web_url": source_metadata.get("webUrl"),
            "size": source_metadata.get("size"),
        },
        "template_file": template_source,
        "extraction_summary": {
            "page_count": raw_extraction.get("page_count"),
            "annotation_count": raw_extraction.get("annotation_count"),
            "markup_count": raw_extraction.get("markup_count"),
            "notes": raw_extraction.get("extraction_notes", []),
            "structured_item_count": len(structured_content.get("extracted_items", [])),
        },
        "uploaded_file": {
            "id": upload_metadata.get("id"),
            "name": upload_metadata.get("name"),
            "web_url": upload_metadata.get("webUrl"),
            "size": upload_metadata.get("size"),
        },
        "local_paths": local_paths,
    }


def resolve_template_path(
    *,
    graph_client: GraphClient,
    output_dir: Path,
    input_drive_id: str,
    logger: logging.Logger,
    template_drive_id: str | None = None,
    template_file_id: str | None = None,
    template_file_path: str | None = None,
    local_template_path: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    if not template_file_id and not template_file_path:
        resolved_local_template_path = Path(local_template_path or "templates/report_template.docx").expanduser().resolve()
        return resolved_local_template_path, {
            "source": "local",
            "path": str(resolved_local_template_path),
        }

    if template_file_id and template_file_path:
        raise ValueError("Provide only one of template_file_id or template_file_path")

    resolved_template_drive_id = template_drive_id or input_drive_id
    downloaded_template_path = output_dir / "downloaded_template.docx"
    template_metadata = graph_client.download_file(
        resolved_template_drive_id,
        downloaded_template_path,
        item_id=template_file_id,
        item_path=template_file_path,
    )
    actual_template_path = rename_downloaded_file(downloaded_template_path, template_metadata.get("name"))
    logger.info("Downloaded DOCX template: %s", actual_template_path.name)
    return actual_template_path, {
        "source": "graph",
        "drive_id": resolved_template_drive_id,
        "id": template_metadata.get("id"),
        "name": template_metadata.get("name"),
        "web_url": template_metadata.get("webUrl"),
        "size": template_metadata.get("size"),
        "item_id": template_file_id,
        "item_path": template_file_path,
    }


def rename_downloaded_file(downloaded_file_path: Path, source_name: str | None) -> Path:
    if not source_name:
        return downloaded_file_path

    target_path = downloaded_file_path.with_name(source_name)
    downloaded_file_path.replace(target_path)
    return target_path


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
