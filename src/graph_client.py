from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from urllib.parse import quote

import msal
import requests

from .config import GraphSettings


class GraphClientError(RuntimeError):
    """Raised when a Microsoft Graph request fails."""


class GraphClient:
    def __init__(self, settings: GraphSettings, logger: logging.Logger | None = None) -> None:
        self.settings = settings
        self.logger = logger or logging.getLogger(__name__)
        self.session = requests.Session()
        self.app = msal.ConfidentialClientApplication(
            client_id=settings.client_id,
            client_credential=settings.client_secret,
            authority=f"https://login.microsoftonline.com/{settings.tenant_id}",
        )
        self._access_token: str | None = None

    def get_item_metadata(
        self,
        drive_id: str,
        *,
        item_id: str | None = None,
        item_path: str | None = None,
    ) -> dict[str, Any]:
        endpoint = self._build_item_endpoint(drive_id, item_id=item_id, item_path=item_path)
        return self._request_json("GET", endpoint)

    def download_file(
        self,
        drive_id: str,
        destination: Path,
        *,
        item_id: str | None = None,
        item_path: str | None = None,
    ) -> dict[str, Any]:
        metadata = self.get_item_metadata(drive_id, item_id=item_id, item_path=item_path)
        content_endpoint = self._build_item_endpoint(
            drive_id,
            item_id=item_id,
            item_path=item_path,
            suffix="/content",
        )
        response = self._request("GET", content_endpoint, stream=True)
        destination.parent.mkdir(parents=True, exist_ok=True)

        with destination.open("wb") as file_handle:
            for chunk in response.iter_content(chunk_size=1024 * 128):
                if chunk:
                    file_handle.write(chunk)

        return metadata

    def upload_file(
        self,
        drive_id: str,
        source_path: Path,
        file_name: str,
        *,
        parent_folder_id: str | None = None,
        parent_folder_path: str | None = None,
    ) -> dict[str, Any]:
        if bool(parent_folder_id) == bool(parent_folder_path):
            raise ValueError("Provide exactly one of parent_folder_id or parent_folder_path")

        encoded_name = quote(file_name)
        if parent_folder_id:
            endpoint = f"/drives/{drive_id}/items/{parent_folder_id}:/{encoded_name}:/content"
        else:
            normalized_folder = _normalize_graph_path(parent_folder_path)
            endpoint = f"/drives/{drive_id}/root:/{normalized_folder}/{encoded_name}:/content"

        with source_path.open("rb") as file_handle:
            return self._request_json(
                "PUT",
                endpoint,
                headers={"Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
                data=file_handle.read(),
            )

    def _request_json(
        self,
        method: str,
        endpoint: str,
        *,
        headers: dict[str, str] | None = None,
        data: bytes | None = None,
    ) -> dict[str, Any]:
        response = self._request(method, endpoint, headers=headers, data=data)
        return response.json()

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        headers: dict[str, str] | None = None,
        data: bytes | None = None,
        stream: bool = False,
    ) -> requests.Response:
        merged_headers = {"Authorization": f"Bearer {self._get_access_token()}"}
        if headers:
            merged_headers.update(headers)

        response = self.session.request(
            method=method,
            url=f"{self.settings.base_url}{endpoint}",
            headers=merged_headers,
            data=data,
            timeout=60,
            stream=stream,
        )

        if response.ok:
            return response

        try:
            error_payload = response.json()
        except ValueError:
            error_payload = {"raw": response.text}

        raise GraphClientError(
            f"Graph request failed with status {response.status_code}: {error_payload}"
        )

    def _get_access_token(self) -> str:
        if self._access_token:
            return self._access_token

        token_result = self.app.acquire_token_for_client(scopes=[self.settings.scope])
        token = token_result.get("access_token")
        if token:
            self._access_token = token
            return token

        raise GraphClientError(f"Unable to acquire Graph token: {token_result}")

    def _build_item_endpoint(
        self,
        drive_id: str,
        *,
        item_id: str | None = None,
        item_path: str | None = None,
        suffix: str = "",
    ) -> str:
        if bool(item_id) == bool(item_path):
            raise ValueError("Provide exactly one of item_id or item_path")

        if item_id:
            return f"/drives/{drive_id}/items/{item_id}{suffix}"

        normalized_path = _normalize_graph_path(item_path)
        return f"/drives/{drive_id}/root:/{normalized_path}:{suffix}"


def _normalize_graph_path(path: str | None) -> str:
    if not path:
        raise ValueError("A non-empty Graph path is required")

    stripped = path.strip().strip("/")
    if not stripped:
        raise ValueError("A non-empty Graph path is required")

    return quote(stripped, safe="/")
