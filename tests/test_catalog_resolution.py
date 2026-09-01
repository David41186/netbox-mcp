import pytest

from netbox_mcp.catalog import is_known_endpoint
from netbox_mcp.client import NetBoxToolError, resolve_endpoint


def test_known_endpoints_pass_validation():
    assert is_known_endpoint("dcim.devices")
    assert is_known_endpoint("ipam.prefixes")
    assert is_known_endpoint("virtualization.virtual_machines")


@pytest.mark.parametrize(
    "endpoint",
    ["dcim.made_up_thing", "not_an_app.devices", "devices", ""],
)
def test_unknown_endpoints_fail_validation(endpoint):
    assert not is_known_endpoint(endpoint)


def test_resolve_endpoint_rejects_unknown_endpoint_without_hitting_network():
    with pytest.raises(NetBoxToolError):
        resolve_endpoint("dcim.made_up_thing")


def test_resolve_endpoint_returns_matching_pynetbox_endpoint(monkeypatch):
    sentinel = object()

    class FakeApp:
        devices = sentinel

    class FakeClient:
        dcim = FakeApp()

    monkeypatch.setattr("netbox_mcp.client.get_client", lambda: FakeClient())

    assert resolve_endpoint("dcim.devices") is sentinel
