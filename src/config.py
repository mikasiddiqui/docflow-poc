from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class GraphSettings:
    tenant_id: str
    client_id: str
    client_secret: str
    base_url: str
    scope: str
    default_drive_id: str | None
    default_output_drive_id: str | None


@dataclass(frozen=True)
class AppSettings:
    graph: GraphSettings
    output_dir: Path
    log_level: str
    enable_llm_mapping: bool


def load_settings() -> AppSettings:
    load_dotenv()

    graph = GraphSettings(
        tenant_id=_required_env("DOCFLOW_GRAPH_TENANT_ID"),
        client_id=_required_env("DOCFLOW_GRAPH_CLIENT_ID"),
        client_secret=_required_env("DOCFLOW_GRAPH_CLIENT_SECRET"),
        base_url=os.getenv("DOCFLOW_GRAPH_BASE_URL", "https://graph.microsoft.com/v1.0"),
        scope="https://graph.microsoft.com/.default",
        default_drive_id=os.getenv("DOCFLOW_GRAPH_DRIVE_ID"),
        default_output_drive_id=os.getenv("DOCFLOW_GRAPH_OUTPUT_DRIVE_ID"),
    )

    output_dir = Path(os.getenv("DOCFLOW_OUTPUT_DIR", "output")).expanduser().resolve()

    return AppSettings(
        graph=graph,
        output_dir=output_dir,
        log_level=os.getenv("DOCFLOW_LOG_LEVEL", "INFO").upper(),
        enable_llm_mapping=_read_bool("DOCFLOW_ENABLE_LLM_MAPPING", default=False),
    )


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if value:
        return value
    raise ValueError(f"Missing required environment variable: {name}")


def _read_bool(name: str, *, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    return raw_value.strip().lower() in {"1", "true", "yes", "on"}
