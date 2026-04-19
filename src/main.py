from __future__ import annotations

import argparse
import json
import sys

from .config import load_settings
from .graph_client import GraphClient
from .pipeline import configure_logging, process_document


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

    result = process_document(
        settings=settings,
        graph_client=graph_client,
        input_drive_id=input_drive_id,
        input_file_id=args.input_file_id,
        input_file_path=args.input_file_path,
        output_drive_id=output_drive_id,
        output_folder_id=args.output_folder_id,
        output_folder_path=args.output_folder_path,
        template_drive_id=args.template_drive_id,
        template_file_id=args.template_file_id,
        template_file_path=args.template_file_path,
        local_template_path=args.template_path,
        upload_file_name=args.upload_file_name,
        logger=logger,
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "source_file_name": result["source_file_name"],
                "extracted_items": result["extracted_items"],
                "uploaded_file_name": result["uploaded_file_name"],
                "audit_path": result["audit_path"],
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


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"docflow-poc failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
