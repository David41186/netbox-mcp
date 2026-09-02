import pynetbox
import pytest
from pynetbox.core.response import Record

from netbox_mcp.actions import is_known_action
from netbox_mcp.client import (
    NetBoxToolError,
    as_action_result,
    call_detail_endpoint,
    resolve_action,
)


class _FakeHTTPResponse:
    """Minimal stand-in for a requests.Response, matching what
    pynetbox.RequestError / pynetbox.ContentError read off it."""

    def __init__(self, status_code, url, text, reason="", json_error=True):
        self.status_code = status_code
        self.url = url
        self.text = text
        self.reason = reason
        self.request = type("_Req", (), {"body": None})()
        self._json_error = json_error

    def json(self):
        if self._json_error:
            raise ValueError("not json")
        return {}


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


# Regression tests for a bug found in live testing: pynetbox's GET path
# (Request.get(), used by DetailEndpoint.list() with no custom_return) is a
# *lazy generator* — detail.list(**params) returns instantly without making
# any HTTP request. The request, and any exception from it, only happens
# once the result is iterated (inside as_action_result's `list(result)`).
# A try/except around only the `detail.list(...)` call therefore never
# catches the real error — it has to wrap consumption of the result too.
# call_detail_endpoint exists specifically to get this right in one place.


def test_call_detail_endpoint_catches_errors_raised_during_lazy_list_iteration():
    response = _FakeHTTPResponse(
        status_code=405,
        url="https://netbox.example/api/dcim/devices/1/render-config/",
        text='{"detail": "Method \\"GET\\" not allowed."}',
        reason="Method Not Allowed",
    )

    class FakeDetail:
        def list(self, **kwargs):
            def gen():
                raise pynetbox.RequestError(response)
                yield  # pragma: no cover - makes this a generator function

            return gen()

    with pytest.raises(NetBoxToolError):
        call_detail_endpoint(FakeDetail(), "list")


def test_call_detail_endpoint_returns_raw_text_for_a_non_json_success_response():
    response = _FakeHTTPResponse(
        status_code=200,
        url="https://netbox.example/api/dcim/racks/1/elevation/",
        text="<svg>...</svg>",
    )

    class FakeDetail:
        def list(self, **kwargs):
            def gen():
                raise pynetbox.ContentError(response)
                yield  # pragma: no cover - makes this a generator function

            return gen()

    result = call_detail_endpoint(FakeDetail(), "list", params={"render": "svg"})

    assert result == "<svg>...</svg>"


def test_call_detail_endpoint_normalizes_a_successful_list_call():
    class FakeDetail:
        def list(self, **kwargs):
            return [
                Record({"family": 4, "address": "10.0.0.1/24"}, None, None),
                Record({"family": 4, "address": "10.0.0.2/24"}, None, None),
            ]

    result = call_detail_endpoint(FakeDetail(), "list")

    assert result == [
        {"family": 4, "address": "10.0.0.1/24"},
        {"family": 4, "address": "10.0.0.2/24"},
    ]


def test_call_detail_endpoint_normalizes_a_successful_create_call():
    class FakeDetail:
        def create(self, data=None, **kwargs):
            assert data == {"prefix_length": 29}
            return Record({"id": 1, "prefix": "10.0.0.0/29"}, None, None)

    result = call_detail_endpoint(
        FakeDetail(), "create", data={"prefix_length": 29}
    )

    assert result == {"id": 1, "prefix": "10.0.0.0/29"}


def test_call_detail_endpoint_wraps_a_synchronous_create_error():
    response = _FakeHTTPResponse(
        status_code=400,
        url="https://netbox.example/api/ipam/prefixes/1/available-prefixes/",
        text='{"detail": "no space"}',
        reason="Bad Request",
    )

    class FakeDetail:
        def create(self, data=None, **kwargs):
            raise pynetbox.RequestError(response)

    with pytest.raises(NetBoxToolError):
        call_detail_endpoint(FakeDetail(), "create", data={"prefix_length": 29})
