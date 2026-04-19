from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.storage.blob import BlobServiceClient

from .config import AppSettings


class StateStore:
    def read_text(self, key: str) -> str | None:
        raise NotImplementedError

    def write_text(self, key: str, value: str) -> None:
        raise NotImplementedError

    def read_json(self, key: str, default: dict[str, Any] | None = None) -> dict[str, Any]:
        raw_value = self.read_text(key)
        if not raw_value:
            return default or {}
        return json.loads(raw_value)

    def write_json(self, key: str, value: dict[str, Any]) -> None:
        self.write_text(key, json.dumps(value, indent=2))


class BlobStateStore(StateStore):
    def __init__(self, connection_string: str, container_name: str) -> None:
        self.container_name = container_name
        self.client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.client.get_container_client(container_name)
        try:
            self.container_client.create_container()
        except ResourceExistsError:
            pass

    def read_text(self, key: str) -> str | None:
        blob_client = self.container_client.get_blob_client(key)
        try:
            return blob_client.download_blob().readall().decode("utf-8")
        except ResourceNotFoundError:
            return None

    def write_text(self, key: str, value: str) -> None:
        blob_client = self.container_client.get_blob_client(key)
        blob_client.upload_blob(value.encode("utf-8"), overwrite=True)


class FileStateStore(StateStore):
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def read_text(self, key: str) -> str | None:
        path = self.directory / key
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def write_text(self, key: str, value: str) -> None:
        path = self.directory / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")


def create_state_store(settings: AppSettings, logger: logging.Logger | None = None) -> StateStore:
    logger = logger or logging.getLogger(__name__)
    connection_string = os.getenv("AzureWebJobsStorage")
    if connection_string:
        logger.info("Using Azure Blob Storage for trigger state.")
        return BlobStateStore(connection_string, settings.state_container)

    logger.warning("AzureWebJobsStorage not set. Falling back to local state files.")
    return FileStateStore(settings.output_dir / ".state")
