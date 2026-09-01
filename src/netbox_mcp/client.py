"""pynetbox client construction and endpoint resolution."""

from __future__ import annotations

from functools import lru_cache

import pynetbox
from mcp.server.mcpserver.exceptions import ToolError
from pynetbox.core.endpoint import Endpoint

from .catalog import is_known_endpoint
from .config import get_settings


class NetBoxToolError(ToolError):
    """Raised for any tool-facing error; the message is shown verbatim to the LLM."""


@lru_cache(maxsize=1)
def get_client() -> pynetbox.api:
    settings = get_settings()
    nb = pynetbox.api(settings.netbox_url, token=settings.netbox_token)
    nb.http_session.verify = settings.verify_ssl
    return nb


def resolve_endpoint(endpoint: str) -> Endpoint:
    """Resolve an "app.endpoint" string (e.g. "dcim.devices") to a pynetbox Endpoint.

    Validates against the curated catalog first so unknown strings produce a
    clear error instead of an opaque AttributeError.
    """
    if not is_known_endpoint(endpoint):
        raise NetBoxToolError(
            f"Unknown endpoint '{endpoint}'. Call netbox_list_endpoints to see "
            "the supported app.endpoint values."
        )
    app_name, _, endpoint_name = endpoint.partition(".")
    nb = get_client()
    app = getattr(nb, app_name)
    return getattr(app, endpoint_name)


def as_dict(record) -> dict:
    return dict(record)
