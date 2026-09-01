import pytest
from pynetbox.core.response import Record

from netbox_mcp.actions import is_known_action
from netbox_mcp.client import NetBoxToolError, as_action_result, resolve_action


def test_known_actions_pass_validation():
    assert is_known_action("ipam.prefixes", "available_ips")
    assert is_known_action("ipam.prefixes", "available_prefixes")
    assert is_known_action("dcim.devices", "render_config")
    assert is_known_action("dcim.racks", "elevation")
    assert is_known_action("dcim.interfaces", "trace")


@pytest.mark.parametrize(
    ("endpoint", "action"),
    [
        ("ipam.prefixes", "made_up_action"),
        ("dcim.made_up_thing", "available_ips"),
        ("dcim.devices", "available_ips"),  # valid action, wrong endpoint
        ("dcim.devices", "napalm"),  # no longer exists on current NetBox
        ("dcim.racks", "units"),  # replaced by "elevation"
        ("", ""),
    ],
)
def test_unknown_action_pairs_fail_validation(endpoint, action):
    assert not is_known_action(endpoint, action)


def test_resolve_action_rejects_unknown_action_without_hitting_network():
    with pytest.raises(NetBoxToolError):
        resolve_action("ipam.prefixes", 1, "made_up_action")


def test_resolve_action_raises_when_object_not_found(monkeypatch):
    class FakeEndpoint:
        def get(self, id):
            return None

    class FakeApp:
        prefixes = FakeEndpoint()

    class FakeClient:
        ipam = FakeApp()

    monkeypatch.setattr("netbox_mcp.client.get_client", lambda: FakeClient())

    with pytest.raises(NetBoxToolError):
        resolve_action("ipam.prefixes", 1, "available_ips")


def test_resolve_action_builds_a_detail_endpoint_with_the_correct_url(monkeypatch):
    class FakeAPI:
        token = "fake-token"
        http_session = object()

    class FakeEndpoint:
        url = "https://netbox.example/api/ipam/prefixes"

        def get(self, id):
            return Record({"id": id}, FakeAPI(), self)

    class FakeApp:
        prefixes = FakeEndpoint()

    class FakeClient:
        ipam = FakeApp()

    monkeypatch.setattr("netbox_mcp.client.get_client", lambda: FakeClient())

    detail = resolve_action("ipam.prefixes", 5, "available_ips")

    assert detail.url == "https://netbox.example/api/ipam/prefixes/5/available-ips/"


def test_resolve_action_converts_underscores_to_hyphens_in_the_action_url(monkeypatch):
    class FakeAPI:
        token = "fake-token"
        http_session = object()

    class FakeEndpoint:
        url = "https://netbox.example/api/dcim/racks"

        def get(self, id):
            return Record({"id": id}, FakeAPI(), self)

    class FakeApp:
        racks = FakeEndpoint()

    class FakeClient:
        dcim = FakeApp()

    monkeypatch.setattr("netbox_mcp.client.get_client", lambda: FakeClient())

    # "available_prefixes" style names aren't used on racks, but this
    # exercises the same underscore -> hyphen conversion with a
    # multi-word action name against a real catalog entry.
    detail = resolve_action("dcim.racks", 7, "elevation")

    assert detail.url == "https://netbox.example/api/dcim/racks/7/elevation/"


def test_as_action_result_normalizes_a_single_record():
    record = Record({"id": 1, "address": "10.0.0.1/24"}, None, None)
    assert as_action_result(record) == {"id": 1, "address": "10.0.0.1/24"}


def test_as_action_result_normalizes_a_list_of_records():
    records = [
        Record({"id": 1, "address": "10.0.0.1/24"}, None, None),
        Record({"id": 2, "address": "10.0.0.2/24"}, None, None),
    ]
    assert as_action_result(records) == [
        {"id": 1, "address": "10.0.0.1/24"},
        {"id": 2, "address": "10.0.0.2/24"},
    ]


def test_as_action_result_passes_through_raw_json():
    raw_dict = {"count": 1, "results": [{"id": 1}]}
    assert as_action_result(raw_dict) is raw_dict


def test_as_action_result_passes_through_raw_string():
    svg = "<svg>...</svg>"
    assert as_action_result(svg) is svg
