"""Curated catalog of NetBox REST API endpoints exposed to the MCP tools.

NetBox has well over a hundred object types. Rather than hand-writing a tool
per type, the generic CRUD tools in tools.py take an "app.endpoint" string
(e.g. "dcim.devices") and this catalog is the whitelist of strings they
accept, grouped by NetBox app with a short description of each. It also
powers the netbox_list_endpoints discovery tool so the LLM can see what's
available without guessing.
"""

from __future__ import annotations

CATALOG: dict[str, dict[str, str]] = {
    "dcim": {
        "sites": "Physical sites / locations",
        "locations": "Sub-site locations (buildings, floors, rooms)",
        "racks": "Equipment racks",
        "rack_roles": "Functional roles assigned to racks",
        "manufacturers": "Hardware manufacturers",
        "device_types": "Device hardware models",
        "device_roles": "Functional roles assigned to devices",
        "platforms": "Device operating systems / platforms",
        "devices": "Network devices, servers, and appliances",
        "interfaces": "Device network interfaces",
        "cables": "Physical cable connections between components",
        "console_ports": "Device console ports",
        "console_server_ports": "Console server ports",
        "power_ports": "Device power ports",
        "power_outlets": "Device power outlets",
        "power_panels": "Power distribution panels",
        "power_feeds": "Power feeds into panels",
        "virtual_chassis": "Stacked/virtual chassis groupings of devices",
        "inventory_items": "Discrete hardware components within a device",
    },
    "ipam": {
        "aggregates": "Top-level IP address aggregates (RIR allocations)",
        "prefixes": "IP prefixes / subnets",
        "ip_ranges": "Ranges of IP addresses within a prefix",
        "ip_addresses": "Individual IP address assignments",
        "vlans": "VLANs",
        "vlan_groups": "Groupings of VLANs sharing an ID space",
        "vrfs": "Virtual routing and forwarding instances",
        "route_targets": "VRF/VPN route targets",
        "rirs": "Regional Internet Registries",
        "roles": "Functional roles for prefixes/VLANs",
        "asns": "Autonomous system numbers",
        "fhrp_groups": "First-hop redundancy protocol groups (VRRP/HSRP)",
        "services": "Network services running on devices/VMs",
    },
    "circuits": {
        "providers": "Circuit providers (carriers/ISPs)",
        "provider_networks": "Provider-side networks",
        "circuits": "Circuits leased from providers",
        "circuit_types": "Circuit type classifications",
        "circuit_terminations": "Endpoints where circuits terminate",
    },
    "virtualization": {
        "cluster_types": "Virtualization cluster types",
        "cluster_groups": "Groupings of clusters",
        "clusters": "Virtualization clusters",
        "virtual_machines": "Virtual machines",
        "interfaces": "Virtual machine network interfaces",
    },
    "tenancy": {
        "tenants": "Customers/organizations that own resources",
        "tenant_groups": "Groupings of tenants",
        "contacts": "Contact records",
        "contact_groups": "Groupings of contacts",
        "contact_roles": "Functional roles for contacts",
    },
    "extras": {
        "tags": "Tags applied across object types",
        "custom_fields": "Custom field definitions",
        "custom_links": "Custom links shown on object pages",
        "journal_entries": "Free-form journal entries attached to objects",
        "config_contexts": "Configuration context data",
    },
    "users": {
        "users": "NetBox user accounts",
        "groups": "User groups",
    },
    "vpn": {
        "tunnels": "VPN tunnels",
        "tunnel_groups": "Groupings of VPN tunnels",
        "ike_policies": "IKE policies",
        "ipsec_policies": "IPSec policies",
        "l2vpns": "Layer 2 VPNs",
    },
    "wireless": {
        "wireless_lans": "Wireless LANs",
        "wireless_lan_groups": "Groupings of wireless LANs",
        "wireless_links": "Point-to-point wireless links",
    },
}


def is_known_endpoint(endpoint: str) -> bool:
    app, _, name = endpoint.partition(".")
    return name != "" and name in CATALOG.get(app, {})


def describe_catalog() -> dict[str, dict[str, str]]:
    return CATALOG
