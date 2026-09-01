"""pynetbox client construction and endpoint resolution."""

from __future__ import annotations

from functools import lru_cache

import pynetbox
from mcp.server.mcpserver.exceptions import ToolError
from pynetbox.core.endpoint import DetailEndpoint, Endpoint
from pynetbox.core.response import Record

from .actions import is_known_action
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


def resolve_action(endpoint: str, id: int, action: str) -> DetailEndpoint:
    """Resolve an "app.endpoint" + numeric id + action name to a pynetbox
    DetailEndpoint (a "server-side call" beyond plain CRUD, e.g.
    "available_ips" on a prefix or "trace" on an interface).

    Validates against the actions catalog first, then fetches the specific
    record. The DetailEndpoint is built directly from the action name
    (converted to NetBox's hyphenated URL form) rather than via pynetbox's
    per-model convenience properties (e.g. Prefixes.available_ips): those
    lag the live NetBox schema — see the note in actions.py — so building
    it directly here means every catalog entry works the same way whether
    or not pynetbox happens to model it.
    """
    if not is_known_action(endpoint, action):
        raise NetBoxToolError(
            f"Unknown action '{action}' for endpoint '{endpoint}'. Call "
            "netbox_list_actions to see the supported actions."
        )
    ep = resolve_endpoint(endpoint)
    try:
        record = ep.get(id)
    except pynetbox.RequestError as exc:
        raise NetBoxToolError(str(exc)) from exc
    if record is None:
        raise NetBoxToolError(f"No object found at '{endpoint}' with id {id}.")
    return DetailEndpoint(record, action.replace("_", "-"))


def as_action_result(result):
    """Normalize a DetailEndpoint call's return value into something
    JSON-serializable for the MCP client.

    Since `resolve_action` builds DetailEndpoints generically (no
    `custom_return`), a "list" call's result comes back as pynetbox's raw
    generator of dicts (it paginates internally) rather than a list of
    Records — this materializes that generator. A single Record, a raw
    dict (e.g. a render-config response), and a raw string (e.g. an SVG
    rack elevation) are each passed through appropriately.
    """
    if isinstance(result, (dict, str)):
        return result
    if isinstance(result, Record):
        return as_dict(result)
    try:
        items = list(result)
    except TypeError:
        return result
    return [as_dict(item) if isinstance(item, Record) else item for item in items]
