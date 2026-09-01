# netbox-mcp

An MCP server that gives an LLM read and write access to a [NetBox](https://netboxlabs.com/) installation over its REST API.

By default it points at the public demo instance at `https://demo.netbox.dev`. Point it at your own NetBox installation later by changing two environment variables — no code changes needed.

## Tools

Rather than one tool per NetBox object type (there are 100+), this server exposes a small set of generic tools that operate on any endpoint:

- `netbox_list_endpoints` — list every supported `app.endpoint` value (e.g. `dcim.devices`, `ipam.prefixes`), grouped by NetBox app.
- `netbox_get_schema(endpoint)` — get field definitions (required fields, types, valid choices) for an endpoint before writing to it.
- `netbox_list_objects(endpoint, filters=None, limit=50)` — list/search objects.
- `netbox_get_object(endpoint, id)` — get a single object by ID.
- `netbox_create_object(endpoint, data)` — create a new object.
- `netbox_update_object(endpoint, id, data)` — partially update an object.
- `netbox_delete_object(endpoint, id, confirm=True)` — delete an object (requires explicit confirmation).
- `netbox_list_actions` — list every supported server-side "action" (beyond plain CRUD), e.g. allocating the next available IP/prefix/VLAN/ASN, tracing a cable path, rendering a device's config, a rack's elevation, or triggering a data source sync.
- `netbox_call_action(endpoint, id, action, method="list", params=None, data=None)` — call one of those actions on a specific object.

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env
```

Edit `.env`:

- `NETBOX_URL` — your NetBox instance, e.g. `https://demo.netbox.dev` or your own install.
- `NETBOX_TOKEN` — an API token from your NetBox user profile (**Admin > API Tokens**). Required for both reads and writes. For the public demo, [create a free account](https://demo.netbox.dev/plugins/demo/login/) (it's reset periodically) then generate a token from your user profile.
- `NETBOX_MCP_READ_ONLY` — set to `true` to disable all create/update/delete tools. Recommended until you're confident in the setup, especially against a real installation.
- `NETBOX_VERIFY_SSL` — set to `false` only if your instance uses a self-signed certificate.

## Running

```bash
uv run netbox-mcp
```

This runs the server over stdio, which is how MCP clients like Claude Code and Claude Desktop launch it.

### Try it interactively

```bash
uv run mcp dev src/netbox_mcp/server.py
```

Opens the MCP Inspector so you can call tools directly and see NetBox's responses before wiring the server into a client.

### Connect to Claude Code

Add to `.mcp.json` in your project (or user-level MCP config):

```json
{
  "mcpServers": {
    "netbox": {
      "command": "uv",
      "args": ["--directory", "/path/to/netbox-mcp", "run", "netbox-mcp"],
      "env": {
        "NETBOX_URL": "https://demo.netbox.dev",
        "NETBOX_TOKEN": "your-api-token",
        "NETBOX_MCP_READ_ONLY": "false"
      }
    }
  }
}
```

### Connect to Claude Desktop

Add the same `netbox` entry under `mcpServers` in your `claude_desktop_config.json`.

## Switching to your own NetBox instance

Change `NETBOX_URL` and `NETBOX_TOKEN` (in `.env`, or in the client's MCP server config) and restart the server. Nothing else changes.

## Example prompts

- "List the sites in NetBox and how many devices are in each."
- "What's the schema for creating a device? I want to add a new switch called sw-core-02."
- "Find all unused IP addresses in the 10.0.0.0/24 prefix."
- "Create a new VLAN 200 named 'guest-wifi' in the site called Amsterdam."

## Tests

```bash
uv run pytest
```
