from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import AppSettings, load_settings
from .docx_generator import generate_docx
from .graph_client import GraphClient
from .mapper import map_to_structured_schema
from .pdf_extractor import extract_pdf_content


def main() -> int:
    args = parse_args()
    settings = load_settings()
    logger = configure_logging(settings)

    if settings.enable_llm_mapping:
        logger.info("LLM mapping flag is enabled, but this POC still uses deterministic mapping only.")

    input_drive_id = args.drive_id or settings.graph.default_drive_id
    if not input_drive_id:
        raise ValueError("An input drive ID is required. Use --drive-id or DOCFLOW_GRAPH_DRIVE_ID.")

    output_drive_id = args.output_drive_id or settings.graph.default_output_drive_id or input_drive_id
    output_dir = settings.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting docflow run")
    graph_client = GraphClient(settings.graph, logger=logger)

    downloaded_pdf_path = output_dir / "downloaded_input.pdf"
    template_path, template_source = resolve_template_path(
        args=args,
        graph_client=graph_client,
        output_dir=output_dir,
        input_drive_id=input_drive_id,
        logger=logger,
    )

    source_metadata = graph_client.download_file(
        input_drive_id,
        downloaded_pdf_path,
        item_id=args.input_file_id,
        item_path=args.input_file_path,
    )

    actual_download_path = _rename_downloaded_file(downloaded_pdf_path, source_metadata.get("name"))
    logger.info("Downloaded source PDF: %s", actual_download_path.name)

    raw_extraction = extract_pdf_content(actual_download_path, logger=logger)
    raw_extraction_path = output_dir / "raw_extraction.json"
    _write_json(raw_extraction_path, raw_extraction)

    structured_content = map_to_structured_schema(raw_extraction)
    structured_content_path = output_dir / "structured_content.json"
    _write_json(structured_content_path, structured_content)

    generated_docx_path = output_dir / "generated_report.docx"
    generate_docx(template_path, structured_content, generated_docx_path)
    logger.info("Generated DOCX: %s", generated_docx_path.name)

    upload_file_name = args.upload_file_name or f"{actual_download_path.stem}-generated.docx"
    upload_metadata = graph_client.upload_file(
        output_drive_id,
        generated_docx_path,
        upload_file_name,
        parent_folder_id=args.output_folder_id,
        parent_folder_path=args.output_folder_path,
    )
    logger.info("Uploaded DOCX to Microsoft storage as: %s", upload_file_name)

    audit_payload = build_audit_payload(
        args=args,
        settings=settings,
        source_metadata=source_metadata,
        raw_extraction=raw_extraction,
        structured_content=structured_content,
        upload_metadata=upload_metadata,
        template_source=template_source,
        local_paths={
            "downloaded_pdf": str(actual_download_path),
            "downloaded_template": str(template_path),
            "raw_extraction": str(raw_extraction_path),
            "structured_content": str(structured_content_path),
            "generated_docx": str(generated_docx_path),
        },
    )
    audit_path = output_dir / "run_audit.json"
    _write_json(audit_path, audit_payload)

    print(
        json.dumps(
            {
                "status": "ok",
                "source_file_name": raw_extraction["source_file_name"],
                "extracted_items": len(structured_content["extracted_items"]),
                "uploaded_file_name": upload_file_name,
                "audit_path": str(audit_path),
            },
            indent=2,
        )
    )

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the docflow POC happy path.")
    parser.add_argument("--drive-id", help="Graph drive ID for the source PDF.")
    parser.add_argument("--output-drive-id", help="Graph drive ID for the output DOCX. Defaults to the input drive.")
    parser.add_argument("--template-drive-id", help="Graph drive ID for the DOCX template. Defaults to the input drive.")
    parser.add_argument(
        "--template-path",
        default="templates/report_template.docx",
        help="Local filesystem path to the DOCX template. Ignored if a Graph template file is provided.",
    )
    parser.add_argument("--template-file-id", help="Graph item ID for the DOCX template.")
    parser.add_argument("--template-file-path", help="Graph path for the DOCX template inside the drive.")
    parser.add_argument(
        "--upload-file-name",
        help="Override the uploaded DOCX file name. Defaults to <source-stem>-generated.docx.",
    )

    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--input-file-id", help="Graph item ID for the source PDF.")
    source_group.add_argument("--input-file-path", help="Graph path for the source PDF inside the drive.")

    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--output-folder-id", help="Graph item ID for the destination folder.")
    target_group.add_argument("--output-folder-path", help="Graph path for the destination folder inside the drive.")

    return parser.parse_args()


def configure_logging(settings: AppSettings) -> logging.Logger:
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(settings.output_dir / "run.log"),
        ],
    )
    return logging.getLogger("docflow")


def build_audit_payload(
    *,
    args: argparse.Namespace,
    settings: AppSettings,
    source_metadata: dict[str, Any],
    raw_extraction: dict[str, Any],
    structured_content: dict[str, Any],
    upload_metadata: dict[str, Any],
    template_source: dict[str, Any],
    local_paths: dict[str, str],
) -> dict[str, Any]:
    return {
        "run_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "inputs": {
            "drive_id": args.drive_id or settings.graph.default_drive_id,
            "input_file_id": args.input_file_id,
            "input_file_path": args.input_file_path,
            "output_drive_id": args.output_drive_id or settings.graph.default_output_drive_id or args.drive_id or settings.graph.default_drive_id,
            "output_folder_id": args.output_folder_id,
            "output_folder_path": args.output_folder_path,
            "template_path": str(Path(args.template_path).expanduser().resolve()),
            "template_drive_id": args.template_drive_id,
            "template_file_id": args.template_file_id,
            "template_file_path": args.template_file_path,
        },
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
    args: argparse.Namespace,
    graph_client: GraphClient,
    output_dir: Path,
    input_drive_id: str,
    logger: logging.Logger,
) -> tuple[Path, dict[str, Any]]:
    if not args.template_file_id and not args.template_file_path:
        local_template_path = Path(args.template_path).expanduser().resolve()
        return local_template_path, {
            "source": "local",
            "path": str(local_template_path),
        }

    if args.template_file_id and args.template_file_path:
        raise ValueError("Provide only one of --template-file-id or --template-file-path")

    template_drive_id = args.template_drive_id or input_drive_id
    downloaded_template_path = output_dir / "downloaded_template.docx"
    template_metadata = graph_client.download_file(
        template_drive_id,
        downloaded_template_path,
        item_id=args.template_file_id,
        item_path=args.template_file_path,
    )
    actual_template_path = _rename_downloaded_file(downloaded_template_path, template_metadata.get("name"))
    logger.info("Downloaded DOCX template: %s", actual_template_path.name)
    return actual_template_path, {
        "source": "graph",
        "drive_id": template_drive_id,
        "id": template_metadata.get("id"),
        "name": template_metadata.get("name"),
        "web_url": template_metadata.get("webUrl"),
        "size": template_metadata.get("size"),
        "item_id": args.template_file_id,
        "item_path": args.template_file_path,
    }


def _rename_downloaded_file(downloaded_pdf_path: Path, source_name: str | None) -> Path:
    if not source_name:
        return downloaded_pdf_path

    target_path = downloaded_pdf_path.with_name(source_name)
    downloaded_pdf_path.replace(target_path)
    return target_path


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"docflow-poc failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
