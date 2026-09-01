# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An MCP server (Python, `mcp[cli]` SDK v2 + `pynetbox`) that exposes a NetBox installation's REST API to an LLM for both reading and writing data. It runs over stdio and is launched by an MCP client (Claude Code, Claude Desktop) via `uv run netbox-mcp`.

## Commands

```bash
uv sync                                   # install deps into .venv
uv run netbox-mcp                         # run the server over stdio
uv run mcp dev src/netbox_mcp/server.py   # MCP Inspector — call tools interactively
uv run pytest                             # run all tests
uv run pytest tests/test_config.py -q     # run a single test file
uv run pytest tests/test_config.py::test_defaults  # run a single test
```

No lint/format tooling is configured yet.

Config comes from environment variables, loaded via `.env` (copy from `.env.example`): `NETBOX_URL`, `NETBOX_TOKEN`, `NETBOX_MCP_READ_ONLY`, `NETBOX_VERIFY_SSL`. See `src/netbox_mcp/config.py`.

## Architecture

NetBox has 100+ object types across its apps (dcim, ipam, circuits, virtualization, tenancy, extras, users, vpn, wireless, core). Instead of one MCP tool per object type, this server exposes **7 generic CRUD tools** (`src/netbox_mcp/tools.py`) parameterized by an `"app.endpoint"` string, e.g. `"dcim.devices"` or `"ipam.prefixes"`:

- `netbox_list_endpoints` / `netbox_get_schema` — discovery, so the LLM can find valid endpoint strings and field definitions without guessing.
- `netbox_list_objects` / `netbox_get_object` — reads.
- `netbox_create_object` / `netbox_update_object` / `netbox_delete_object` — writes.

The request flow through the codebase:

1. `server.py` constructs the `MCPServer` instance and calls `register_tools()` from `tools.py`.
2. Each tool in `tools.py` calls `resolve_endpoint(endpoint)` (`client.py`), which validates the `"app.endpoint"` string against the whitelist in `catalog.py` and returns the corresponding `pynetbox` `Endpoint` object (e.g. `nb.dcim.devices`) via a cached `pynetbox.api` client.
3. Write tools call `_require_write_access()` first, which raises if `NETBOX_MCP_READ_ONLY` is set — this is checked before any network call.
4. `pynetbox.RequestError` (which already carries NetBox's field-level validation messages) is caught centrally in each tool and re-raised as `NetBoxToolError`.

**`NetBoxToolError` (`client.py`) subclasses `mcp.server.mcpserver.exceptions.ToolError`, not the bare `Exception` class.** This matters: the `mcp` SDK only forwards the exception's message verbatim to the LLM for `ToolError` subclasses. Any other exception type is treated as a crash — the client only sees a generic "Error executing tool X" and the real message is dropped to stderr. Any new error path added to a tool must raise `NetBoxToolError` (or another `ToolError` subclass) to stay LLM-visible.

`catalog.py` mirrors NetBox's full REST API surface (all endpoints under `dcim`, `ipam`, `circuits`, `virtualization`, `tenancy`, `extras`, `users`, `vpn`, `wireless`, and `core`) as of when it was last checked against a live instance. It exists both to power the `netbox_list_endpoints` discovery tool and to reject unknown endpoint strings before they reach the network (rather than surfacing a raw `AttributeError` from `pynetbox`'s dynamic attribute access). NetBox occasionally adds endpoints between releases — if one's missing, check the live instance's `/api/<app>/` root (or `nb.http_session.get(f"{settings.netbox_url}/api/<app>/")`) and add it to the relevant app dict in `catalog.py`; `client.py`'s resolution is fully generic, so no other code needs to change.

`netbox_get_schema` bypasses `pynetbox`'s own model layer and calls `nb.http_session.options(endpoint.url)` directly — `pynetbox` has no first-class API for the `OPTIONS` schema/choices endpoint.

## Notes specific to this project

- The `mcp` Python SDK is on a v2 rework (`from mcp.server import MCPServer`, not the `FastMCP` name used in older tutorials/docs). Verify against the installed package (`.venv/lib/python3.12/site-packages/mcp/`) rather than trusting cached documentation, since this changed recently.
- `demo.netbox.dev` (the default `NETBOX_URL`) requires an authenticated token for reads, not just writes — there is no anonymous access. Get one at `https://demo.netbox.dev/plugins/demo/login/`.
- Tests mock `pynetbox` (`netbox_mcp.client.get_client`) rather than hitting the network; there is no live-NetBox integration test in the suite.
