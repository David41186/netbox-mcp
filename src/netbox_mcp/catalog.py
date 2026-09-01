"""Full catalog of NetBox REST API endpoints exposed to the MCP tools.

NetBox has well over a hundred object types. Rather than hand-writing a tool
per type, the generic CRUD tools in tools.py take an "app.endpoint" string
(e.g. "dcim.devices") and this catalog is the whitelist of strings they
accept, grouped by NetBox app with a short description of each. It also
powers the netbox_list_endpoints discovery tool so the LLM can see what's
available without guessing.

Endpoint keys are the underscored form of NetBox's REST URL segment (e.g.
"device_types" for "/api/dcim/device-types/"): pynetbox's Endpoint class
converts underscores back to hyphens when building the URL, so this mapping
is mechanical and 1:1 for every endpoint below.

This list mirrors NetBox's own API root (`/api/<app>/`) as of the version
this server was last checked against. NetBox occasionally adds new
endpoints between releases; if `netbox_list_endpoints` is missing something
you expect, check the live instance's `/api/<app>/` root and add it here —
resolution in client.py is fully generic, so adding a catalog entry is
enough to make a new endpoint usable.
"""

from __future__ import annotations

CATALOG: dict[str, dict[str, str]] = {
    "dcim": {
        "regions": "Geographic regions used to group sites",
        "site_groups": "Groupings of sites",
        "sites": "Physical sites / locations",
        "locations": "Sub-site locations (buildings, floors, rooms)",
        "rack_groups": "Groupings of racks (rows/rooms) within a site or location",
        "rack_roles": "Functional roles assigned to racks",
        "rack_types": "Reusable rack hardware models (manufacturer/model/u-height)",
        "racks": "Equipment racks",
        "rack_reservations": "Reserved unit ranges within a rack",
        "manufacturers": "Hardware manufacturers",
        "device_types": "Device hardware models",
        "module_types": "Module hardware models installable into device module bays",
        "module_type_profiles": "Shared attribute profiles reused across module types",
        "device_roles": "Functional roles assigned to devices",
        "platforms": "Device operating systems / platforms",
        "devices": "Network devices, servers, and appliances",
        "modules": "Installed hardware modules within a device's module bays",
        "virtual_device_contexts": "Virtual routing/switching contexts within a single physical device",
        "virtual_chassis": "Stacked/virtual chassis groupings of devices",
        "interfaces": "Device network interfaces",
        "mac_addresses": "MAC addresses assignable to interfaces",
        "console_ports": "Device console ports",
        "console_server_ports": "Console server ports",
        "power_ports": "Device power ports",
        "power_outlets": "Device power outlets",
        "front_ports": "Device front-facing pass-through ports",
        "rear_ports": "Device rear-facing pass-through ports",
        "device_bays": "Bays for housing child devices (e.g. blade chassis slots)",
        "module_bays": "Bays for housing installable modules",
        "inventory_items": "Discrete hardware components within a device",
        "inventory_item_roles": "Functional roles assigned to inventory items",
        "console_port_templates": "Console port templates defined on a device type",
        "console_server_port_templates": "Console server port templates defined on a device type",
        "power_port_templates": "Power port templates defined on a device type",
        "power_outlet_templates": "Power outlet templates defined on a device type",
        "interface_templates": "Interface templates defined on a device type",
        "front_port_templates": "Front port templates defined on a device type",
        "rear_port_templates": "Rear port templates defined on a device type",
        "device_bay_templates": "Device bay templates defined on a device type",
        "module_bay_templates": "Module bay templates defined on a device type",
        "inventory_item_templates": "Inventory item templates defined on a device type",
        "power_panels": "Power distribution panels",
        "power_feeds": "Power feeds into panels",
        "cables": "Physical cable connections between components",
        "cable_terminations": "Individual endpoint terminations of a cable",
        "cable_bundles": "Named bundles grouping multiple cables together",
        "connected_device": "Read-only lookup of the device connected to a given peer device/interface",
    },
    "ipam": {
        "aggregates": "Top-level IP address aggregates (RIR allocations)",
        "asns": "Autonomous system numbers",
        "asn_ranges": "Reusable ranges for allocating ASNs",
        "prefixes": "IP prefixes / subnets",
        "ip_ranges": "Ranges of IP addresses within a prefix",
        "ip_addresses": "Individual IP address assignments",
        "vlans": "VLANs",
        "vlan_groups": "Groupings of VLANs sharing an ID space",
        "vlan_translation_policies": "VLAN ID translation policies",
        "vlan_translation_rules": "Individual VLAN ID translation rules within a policy",
        "vrfs": "Virtual routing and forwarding instances",
        "route_targets": "VRF/VPN route targets",
        "rirs": "Regional Internet Registries",
        "roles": "Functional roles for prefixes/VLANs",
        "fhrp_groups": "First-hop redundancy protocol groups (VRRP/HSRP)",
        "fhrp_group_assignments": "Interface assignments to FHRP groups",
        "services": "Network services running on devices/VMs",
        "service_templates": "Reusable templates for defining services",
    },
    "circuits": {
        "providers": "Circuit providers (carriers/ISPs)",
        "provider_accounts": "Account records held with a provider",
        "provider_networks": "Provider-side networks",
        "circuit_types": "Circuit type classifications",
        "circuits": "Circuits leased from providers",
        "circuit_terminations": "Endpoints where circuits terminate",
        "circuit_groups": "Groupings of related circuits",
        "circuit_group_assignments": "Circuit membership within a circuit group",
        "virtual_circuit_types": "Virtual circuit type classifications",
        "virtual_circuits": "Logical circuits carried over shared physical circuits (e.g. pseudowires)",
        "virtual_circuit_terminations": "Endpoints where virtual circuits terminate",
    },
    "virtualization": {
        "cluster_types": "Virtualization cluster types",
        "cluster_groups": "Groupings of clusters",
        "clusters": "Virtualization clusters",
        "virtual_machine_types": "Reusable VM hardware/sizing profiles",
        "virtual_machines": "Virtual machines",
        "interfaces": "Virtual machine network interfaces",
        "virtual_disks": "Virtual disks attached to a virtual machine",
    },
    "tenancy": {
        "tenant_groups": "Groupings of tenants",
        "tenants": "Customers/organizations that own resources",
        "contact_groups": "Groupings of contacts",
        "contact_roles": "Functional roles for contacts",
        "contacts": "Contact records",
        "contact_assignments": "Assignments of contacts to other objects",
    },
    "extras": {
        "tags": "Tags applied across object types",
        "custom_fields": "Custom field definitions",
        "custom_field_choice_sets": "Reusable choice lists for select-type custom fields",
        "custom_links": "Custom links shown on object pages",
        "export_templates": "Custom templates for exporting object lists",
        "saved_filters": "Reusable saved search filters",
        "table_configs": "Saved table column/sort configurations",
        "bookmarks": "A user's bookmarked objects",
        "notifications": "In-app notifications for a user",
        "notification_groups": "Groups of users/roles that receive notifications",
        "subscriptions": "A user's subscriptions to object change notifications",
        "config_contexts": "Configuration context data",
        "config_context_profiles": "Named profiles that scope config context rendering",
        "config_templates": "Jinja2 templates for rendering device/VM configuration",
        "event_rules": "Rules that trigger webhooks/scripts on object events",
        "webhooks": "HTTP callback definitions triggered by event rules",
        "scripts": "Custom Python scripts runnable from NetBox",
        "journal_entries": "Free-form journal entries attached to objects",
        "image_attachments": "Images attached to other objects",
        "tagged_objects": "Read-only lookup of objects carrying a given tag",
    },
    "users": {
        "users": "NetBox user accounts",
        "groups": "User groups",
        "permissions": "Object-level permission assignments",
        "tokens": "API authentication tokens",
        "owners": "Assignable ownership records for objects",
        "owner_groups": "Groupings of owners used for object ownership assignment",
        "config": "The current user's UI preferences/config",
    },
    "vpn": {
        "tunnel_groups": "Groupings of VPN tunnels",
        "tunnels": "VPN tunnels",
        "tunnel_terminations": "Endpoints where a tunnel terminates on a device/VM interface",
        "ike_proposals": "IKE phase 1 proposal parameters",
        "ike_policies": "IKE policies",
        "ipsec_proposals": "IPSec phase 2 proposal parameters",
        "ipsec_policies": "IPSec policies",
        "ipsec_profiles": "Combined IKE+IPSec profiles applied to tunnels",
        "l2vpns": "Layer 2 VPNs",
        "l2vpn_terminations": "Endpoints where an L2VPN terminates",
    },
    "wireless": {
        "wireless_lan_groups": "Groupings of wireless LANs",
        "wireless_lans": "Wireless LANs",
        "wireless_links": "Point-to-point wireless links",
    },
    "core": {
        "data_sources": "External data sources synced into NetBox (e.g. git repositories)",
        "data_files": "Individual files synced from a data source",
        "jobs": "Background job records and their status",
        "object_changes": "Change history log for tracked objects",
        "object_types": "Read-only registry of NetBox's content types",
        "background_queues": "Read-only status of background task queues",
        "background_tasks": "Individual queued/running background tasks",
        "background_workers": "Background worker process status",
    },
}


def is_known_endpoint(endpoint: str) -> bool:
    app, _, name = endpoint.partition(".")
    return name != "" and name in CATALOG.get(app, {})


def describe_catalog() -> dict[str, dict[str, str]]:
    return CATALOG
