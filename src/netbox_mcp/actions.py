"""Catalog of NetBox "detail" (server-side) actions exposed to the MCP tools.

Beyond plain CRUD, NetBox exposes sub-endpoints on specific objects for
operations that don't fit the REST resource model: allocating the next
available IP/prefix/VLAN/ASN, tracing a cable path, rendering a device's,
VM's, or config template's content, fetching a rack's unit elevation,
syncing an object from its data source, or controlling a background task.

This catalog was built by pulling the live OpenAPI schema from a running
NetBox instance (`GET /api/schema/?format=json`) and extracting every path
matching `/api/<app>/<endpoint>/{id}/<action>/`, then checking which HTTP
methods each one actually supports — deliberately *not* by trusting
pynetbox's bundled model classes, several of which turned out to be stale
(pynetbox still models a `napalm` action and rack `units`, neither of
which exist on NetBox 4.6.9 — `elevation` replaced `units`, and NAPALM
integration was dropped from core). `resolve_action` in client.py builds
each `DetailEndpoint` directly from the action name rather than via
pynetbox's per-model properties, so a listed action works the same way
whether or not pynetbox happens to model it.

Each description notes which HTTP method(s) NetBox actually accepts:
"list" (GET, via netbox_call_action's default method="list") and/or
"create" (POST, via method="create"). Calling the unsupported one for a
given action will surface NetBox's own 404/405 as a NetBoxToolError.
Re-pull the schema periodically to catch NetBox additions/removals; this
is a whitelist, so nothing here works until it's added.
"""

from __future__ import annotations

ACTIONS: dict[str, dict[str, str]] = {
    "ipam.prefixes": {
        "available_ips": (
            "GET: list unallocated IPs in this prefix. POST: allocate one "
            "or more as new ipam.ip_addresses records (data may be a "
            "single {} or a list of {} for bulk, optionally with extra "
            "fields like description)."
        ),
        "available_prefixes": (
            "GET: list unallocated child prefixes within this prefix. "
            'POST: carve out the next available child prefix (data must '
            'include prefix_length, e.g. {"prefix_length": 29}).'
        ),
    },
    "ipam.ip_ranges": {
        "available_ips": (
            "GET: list unallocated IPs in this range. POST: allocate one "
            "or more as new ipam.ip_addresses records (data may be a "
            "single {} or a list of {} for bulk)."
        ),
    },
    "ipam.vlan_groups": {
        "available_vlans": (
            "GET: list unassigned VLAN IDs in this group's range. POST: "
            'create the next available VLAN (data should include at '
            'least a name, e.g. {"name": "new-vlan"}).'
        ),
    },
    "ipam.asn_ranges": {
        "available_asns": (
            "GET: list unassigned ASNs in this range. POST: allocate one "
            "or more (data may be a single {} or a list of {} for bulk)."
        ),
    },
    "dcim.devices": {
        "render_config": (
            "POST only: render this device's configuration from its "
            "assigned config template (data is optional extra context to "
            "merge in; omit for none)."
        ),
    },
    "dcim.racks": {
        "elevation": (
            "GET only: this rack's elevation — structured data listing "
            "what occupies each U by default, or a raw SVG image if "
            'params includes {"render": "svg"}.'
        ),
    },
    "dcim.interfaces": {
        "trace": (
            "GET only: trace the physical cable path from this interface "
            "to its far end, listing every cable/panel hop."
        ),
    },
    "dcim.console_ports": {
        "trace": (
            "GET only: trace the physical cable path from this console "
            "port to its far end."
        ),
    },
    "dcim.console_server_ports": {
        "trace": (
            "GET only: trace the physical cable path from this console "
            "server port to its far end."
        ),
    },
    "dcim.power_ports": {
        "trace": (
            "GET only: trace the physical cable path from this power "
            "port to its far end."
        ),
    },
    "dcim.power_outlets": {
        "trace": (
            "GET only: trace the physical cable path from this power "
            "outlet to its far end."
        ),
    },
    "dcim.power_feeds": {
        "trace": (
            "GET only: trace the physical cable path from this power "
            "feed to its far end (e.g. the PDU it powers)."
        ),
    },
    "dcim.front_ports": {
        "paths": (
            "GET only: list the cable path(s) passing through this front "
            "port."
        ),
    },
    "dcim.rear_ports": {
        "paths": (
            "GET only: list the cable path(s) passing through this rear "
            "port."
        ),
    },
    "circuits.circuit_terminations": {
        "paths": (
            "GET only: list the cable path(s) passing through this "
            "circuit termination."
        ),
    },
    "circuits.virtual_circuit_terminations": {
        "paths": (
            "GET only: list the cable path(s) passing through this "
            "virtual circuit termination."
        ),
    },
    "virtualization.virtual_machines": {
        "render_config": (
            "POST only: render this VM's configuration from its assigned "
            "config template (data is optional extra context to merge "
            "in; omit for none)."
        ),
    },
    "extras.config_templates": {
        "render": (
            "POST only: render this template standalone against arbitrary "
            "context data (data is the context dict to render with)."
        ),
        "sync": (
            "POST only: re-sync this template's content from its data "
            "source (takes no data)."
        ),
    },
    "extras.config_contexts": {
        "sync": (
            "POST only: re-sync this config context's data from its data "
            "source (takes no data)."
        ),
    },
    "extras.config_context_profiles": {
        "sync": (
            "POST only: re-sync this config context profile from its "
            "data source (takes no data)."
        ),
    },
    "extras.export_templates": {
        "sync": (
            "POST only: re-sync this export template's content from its "
            "data source (takes no data)."
        ),
    },
    "extras.custom_field_choice_sets": {
        "choices": (
            "GET only: list the predefined choice values for this custom "
            "field choice set."
        ),
    },
    "core.data_sources": {
        "sync": (
            "POST only: trigger a background sync of this data source "
            "from its remote origin (takes no data)."
        ),
    },
    "core.background_tasks": {
        "delete": (
            "POST only: remove this queued/failed background task (takes "
            "no data). This is a NetBox action route, not the object's "
            "own DELETE — background tasks live in Redis, not the "
            "database, so netbox_delete_object doesn't apply to them."
        ),
        "enqueue": (
            "POST only: enqueue this scheduled/deferred background task "
            "to run now (takes no data)."
        ),
        "requeue": (
            "POST only: requeue this failed background task for another "
            "attempt (takes no data)."
        ),
        "stop": (
            "POST only: stop this currently-running background task "
            "(takes no data)."
        ),
    },
}


def is_known_action(endpoint: str, action: str) -> bool:
    return action in ACTIONS.get(endpoint, {})


def describe_actions() -> dict[str, dict[str, str]]:
    return ACTIONS
