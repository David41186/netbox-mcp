"""Generic MCP tools that operate on any NetBox endpoint listed in the catalog."""

from __future__ import annotations

from typing import Any

import pynetbox
from mcp.server import MCPServer

from .catalog import describe_catalog
from .client import NetBoxToolError, as_dict, get_client, resolve_endpoint
from .config import get_settings


def _require_write_access() -> None:
    if get_settings().read_only:
        raise NetBoxToolError(
            "This server is running in read-only mode (NETBOX_MCP_READ_ONLY=true). "
            "Writes are disabled."
        )


def register_tools(mcp: MCPServer) -> None:
    @mcp.tool()
    def netbox_list_endpoints() -> dict[str, dict[str, str]]:
        """List every supported NetBox 'app.endpoint' value, grouped by app,
        with a short description of what each endpoint represents. Call this
        first to discover which endpoint strings are valid for the other tools.
        """
        return describe_catalog()

    @mcp.tool()
    def netbox_get_schema(endpoint: str) -> dict[str, Any]:
        """Get field definitions for a NetBox endpoint (names, types, whether
        required/read-only, and valid choice values), via an authenticated
        OPTIONS request. Use this before creating or updating objects to see
        what fields are valid.

        Args:
            endpoint: An "app.endpoint" string, e.g. "dcim.devices". See
                netbox_list_endpoints for valid values.
        """
        ep = resolve_endpoint(endpoint)
        nb = get_client()
        try:
            response = nb.http_session.options(ep.url)
            response.raise_for_status()
        except Exception as exc:  # requests.RequestException, etc.
            raise NetBoxToolError(f"Failed to fetch schema for '{endpoint}': {exc}") from exc
        body = response.json()
        return body.get("actions", body)

    @mcp.tool()
    def netbox_list_objects(
        endpoint: str,
        filters: dict[str, Any] | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List/search objects at a NetBox endpoint.

        Args:
            endpoint: An "app.endpoint" string, e.g. "ipam.prefixes". See
                netbox_list_endpoints for valid values.
            filters: Optional field filters applied server-side, e.g.
                {"site": "ams1", "status": "active"}. Omit to list all objects.
            limit: Maximum number of objects to return (default 50, use 0 for
                no limit).
        """
        ep = resolve_endpoint(endpoint)
        try:
            if filters:
                records = ep.filter(**filters)
            else:
                records = ep.all()
            results = []
            for i, record in enumerate(records):
                if limit and i >= limit:
                    break
                results.append(as_dict(record))
            return results
        except pynetbox.RequestError as exc:
            raise NetBoxToolError(str(exc)) from exc

    @mcp.tool()
    def netbox_get_object(endpoint: str, id: int) -> dict[str, Any]:
        """Get a single object from a NetBox endpoint by its numeric ID.

        Args:
            endpoint: An "app.endpoint" string, e.g. "dcim.devices".
            id: The object's numeric ID.
        """
        ep = resolve_endpoint(endpoint)
        try:
            record = ep.get(id)
        except pynetbox.RequestError as exc:
            raise NetBoxToolError(str(exc)) from exc
        if record is None:
            raise NetBoxToolError(f"No object found at '{endpoint}' with id {id}.")
        return as_dict(record)

    @mcp.tool()
    def netbox_create_object(endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new object at a NetBox endpoint. Disabled when the server
        is running in read-only mode.

        Args:
            endpoint: An "app.endpoint" string, e.g. "dcim.sites".
            data: Field values for the new object. Use netbox_get_schema to
                see required and valid fields first.
        """
        _require_write_access()
        ep = resolve_endpoint(endpoint)
        try:
            record = ep.create(**data)
        except pynetbox.RequestError as exc:
            raise NetBoxToolError(str(exc)) from exc
        return as_dict(record)

    @mcp.tool()
    def netbox_update_object(endpoint: str, id: int, data: dict[str, Any]) -> dict[str, Any]:
        """Partially update an existing object at a NetBox endpoint. Only the
        fields included in `data` are changed. Disabled when the server is
        running in read-only mode.

        Args:
            endpoint: An "app.endpoint" string, e.g. "dcim.devices".
            id: The object's numeric ID.
            data: Field values to change.
        """
        _require_write_access()
        ep = resolve_endpoint(endpoint)
        try:
            record = ep.get(id)
            if record is None:
                raise NetBoxToolError(f"No object found at '{endpoint}' with id {id}.")
            record.update(data)
        except pynetbox.RequestError as exc:
            raise NetBoxToolError(str(exc)) from exc
        return as_dict(record)

    @mcp.tool()
    def netbox_delete_object(endpoint: str, id: int, confirm: bool = False) -> str:
        """Delete an object from a NetBox endpoint. This is permanent. Requires
        confirm=True to actually perform the deletion, and is disabled when the
        server is running in read-only mode.

        Args:
            endpoint: An "app.endpoint" string, e.g. "dcim.devices".
            id: The object's numeric ID.
            confirm: Must be explicitly set to true to perform the deletion.
        """
        _require_write_access()
        if not confirm:
            raise NetBoxToolError(
                "Refusing to delete without confirmation. Re-call with confirm=True "
                "once you've verified this is the correct object."
            )
        ep = resolve_endpoint(endpoint)
        try:
            record = ep.get(id)
            if record is None:
                raise NetBoxToolError(f"No object found at '{endpoint}' with id {id}.")
            record.delete()
        except pynetbox.RequestError as exc:
            raise NetBoxToolError(str(exc)) from exc
        return f"Deleted '{endpoint}' object with id {id}."
