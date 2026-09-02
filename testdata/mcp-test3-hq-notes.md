# mcp-test3-hq — full-stack live test of netbox_call_action

Built live against `demo.netbox.dev` via the MCP tools to end-to-end
validate the server-side action tools added in this branch
(`netbox_list_actions` / `netbox_call_action`), on top of the existing CRUD
tools. Unlike the earlier `mcp-test-*` / `mcp-test2-*` fixtures (imported
from `mcp_test_network.csv`, IPs assigned as bare records), this one wires
everything the way a real provisioning workflow would: IPs allocated from
a real prefix via the `available_ips` action and bound directly to
interfaces in the same call, then set as each device's `primary_ip4`.

Left in place on the demo instance as a reference example; the demo resets
periodically, so treat the specific object IDs below as illustrative, not
stable.

## What's there

**Site & network**
- Site `mcp-test3-hq`
- VLAN group `mcp-test3-vlans` + VLAN 130 `mcp-test3-mgmt`
- Prefix `10.30.0.0/24`, scoped to the site and VLAN

**Rack:** `mcp-test3-rack-01` (42U)

**Devices**, each with a management interface (`mgmt0`) holding an IP
allocated via `ipam.prefixes` / `available_ips` (`method="create"`,
`assigned_object_type: "dcim.interface"`) and set as `primary_ip4`, plus
real data interfaces cabled into a router → switch → server topology:

| Device | Type | Rack U | Mgmt IP | Data interfaces |
|---|---|---|---|---|
| mcp-test3-rtr-001 | Cisco ASR1001-X | 1 | 10.30.0.1 | Gi0/0/1 → sw-001 |
| mcp-test3-sw-001 | Cisco Catalyst 9200-24P | 2 | 10.30.0.2 | Gi1/0/1 → router, Gi1/0/2 → srv-001, Gi1/0/3 → sw-002 |
| mcp-test3-sw-002 | Cisco Catalyst 9200-24P | 3 | 10.30.0.3 | Gi1/0/1 → sw-001, Gi1/0/2 → srv-002 |
| mcp-test3-srv-001 | Dell PowerEdge R750 | 6–7 | 10.30.0.4 | eth0 → sw-001 |
| mcp-test3-srv-002 | Dell PowerEdge R750 | 8–9 | 10.30.0.5 | eth0 → sw-002 |

All data-interface links are real `dcim.cables`, confirmed with
`netbox_call_action(dcim.interfaces, <id>, "trace")`.

**Power:** panel `mcp-test3-panel-01`, two 30A/208V circuits on the rack:

| Circuit | PDU | U | Feeds | Allocated draw |
|---|---|---|---|---|
| mcp-test3-feed-A | mcp-test3-pdu-01 (APC AP7901) | 20 | router + both switches | 550 W |
| mcp-test3-feed-B | mcp-test3-pdu-02 (APC AP7901) | 21 | both servers | 1000 W |

Each device has a `PSU1` power port cabled to a PDU outlet; each PDU's
`Input` power port is cabled to its feed. Both circuits sit well under the
4,992 VA usable capacity (30A × 208V × 80% max_utilization).

## How it was built (tool sequence)

1. `netbox_create_object` — site, vlan_group, vlan, prefix, rack
2. `netbox_create_object` × 5 — devices, mounted with `position`/`face` set
   directly (no separate elevation-fixup pass needed, unlike the CSV
   import where per-row height data conflicted with itself)
3. `netbox_create_object` — one `mgmt0` interface per device
4. `netbox_call_action(ipam.prefixes, <id>, "available_ips", method="create", data={"assigned_object_type": "dcim.interface", "assigned_object_id": <mgmt0 id>, "description": ...})` × 5
5. `netbox_update_object` — `primary_ip4` on each device
6. `netbox_create_object` — power panel, 2 feeds, 2 PDU devices, power ports
   on all 5 devices, and `dcim.cables` linking PDU inputs to feeds and
   device power ports to PDU outlets
7. `netbox_create_object` — data interfaces (uplinks/downlinks) + `dcim.cables`
   wiring router → switches → servers
8. Verification: `netbox_call_action(dcim.interfaces, <srv-001 eth0 id>, "trace")`
   and `netbox_call_action(dcim.racks, <id>, "elevation")` — both confirmed
   correct.

No bugs found during this build (the one bug this branch surfaced — a
crash on non-JSON action responses — was found and fixed during the
earlier systematic action-by-action test pass, before this build).
