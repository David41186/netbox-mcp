"""Runtime configuration, loaded from environment variables (and a .env file if present)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    netbox_url: str
    netbox_token: str | None
    read_only: bool
    verify_ssl: bool

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            netbox_url=os.environ.get("NETBOX_URL", "https://demo.netbox.dev").rstrip("/"),
            netbox_token=os.environ.get("NETBOX_TOKEN") or None,
            read_only=_env_bool("NETBOX_MCP_READ_ONLY", False),
            verify_ssl=_env_bool("NETBOX_VERIFY_SSL", True),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
