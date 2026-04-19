from __future__ import annotations

import logging
from typing import Any

from .config import AppSettings
from .graph_client import GraphClient
from .pipeline import process_document
from .state_store import StateStore


def poll_and_process_new_pdfs(
    *,
    settings: AppSettings,
    graph_client: GraphClient,
    state_store: StateStore,
    logger: logging.Logger,
) -> dict[str, Any]:
    drive_id = settings.graph.default_drive_id
    if not drive_id:
        raise ValueError("DOCFLOW_GRAPH_DRIVE_ID is required for timer-trigger processing.")

    previous_delta_link = state_store.read_text(settings.delta_link_blob_name)
    processed_items = state_store.read_json(settings.processed_items_blob_name, default={})

    response = graph_client.get_drive_delta(
        drive_id,
        delta_link=previous_delta_link,
        token_latest=previous_delta_link is None and settings.initial_delta_mode == "latest",
    )

    candidate_items: list[dict[str, Any]] = []
    delta_link = None
    while True:
        candidate_items.extend(response.get("value", []))
        next_link = response.get("@odata.nextLink")
        delta_link = response.get("@odata.deltaLink", delta_link)
        if not next_link:
            break
        response = graph_client.get_drive_delta(drive_id, delta_link=next_link)

    processed_runs: list[dict[str, Any]] = []
    input_folder_path = _normalize_path(settings.input_folder_path)

    for item in candidate_items:
        if not _should_process_item(item, input_folder_path=input_folder_path):
            continue

        item_id = item["id"]
        item_version = item.get("eTag") or item.get("cTag") or item.get("lastModifiedDateTime") or ""
        if processed_items.get(item_id) == item_version:
            logger.info("Skipping already processed PDF version: %s", item.get("name"))
            continue

        logger.info("Processing new or updated PDF: %s", item.get("name"))
        result = process_document(
            settings=settings,
            graph_client=graph_client,
            input_drive_id=drive_id,
            input_file_id=item_id,
            output_drive_id=settings.graph.default_output_drive_id or drive_id,
            output_folder_path=settings.output_folder_path,
            template_drive_id=settings.template_drive_id or drive_id,
            template_file_path=settings.template_file_path,
            logger=logger,
        )
        processed_runs.append(
            {
                "item_id": item_id,
                "name": item.get("name"),
                "uploaded_file_name": result["uploaded_file_name"],
            }
        )
        processed_items[item_id] = item_version

    if delta_link:
        state_store.write_text(settings.delta_link_blob_name, delta_link)
    state_store.write_json(settings.processed_items_blob_name, processed_items)

    return {
        "scanned_items": len(candidate_items),
        "processed_items": len(processed_runs),
        "processed_runs": processed_runs,
        "initial_mode": settings.initial_delta_mode,
    }


def _should_process_item(item: dict[str, Any], *, input_folder_path: str) -> bool:
    if item.get("@removed"):
        return False
    if not item.get("file"):
        return False

    name = str(item.get("name", ""))
    if not name.lower().endswith(".pdf"):
        return False

    relative_path = _get_relative_path(item)
    if not relative_path:
        return False

    return relative_path == input_folder_path or relative_path.startswith(f"{input_folder_path}/")


def _get_relative_path(item: dict[str, Any]) -> str:
    parent_path = str(item.get("parentReference", {}).get("path", ""))
    name = str(item.get("name", "")).strip("/")
    if not name:
        return ""

    if "/root:" in parent_path:
        prefix = parent_path.split("/root:", 1)[1].strip("/")
    else:
        prefix = ""

    relative_path = "/".join(part for part in [prefix, name] if part)
    return _normalize_path(relative_path)


def _normalize_path(path: str) -> str:
    return path.strip().strip("/")
