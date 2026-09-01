from netbox_mcp.config import Settings


def test_defaults(monkeypatch):
    for var in ("NETBOX_URL", "NETBOX_TOKEN", "NETBOX_MCP_READ_ONLY", "NETBOX_VERIFY_SSL"):
        monkeypatch.delenv(var, raising=False)

    settings = Settings.from_env()

    assert settings.netbox_url == "https://demo.netbox.dev"
    assert settings.netbox_token is None
    assert settings.read_only is False
    assert settings.verify_ssl is True


def test_overrides_from_env(monkeypatch):
    monkeypatch.setenv("NETBOX_URL", "https://netbox.example.com/")
    monkeypatch.setenv("NETBOX_TOKEN", "abc123")
    monkeypatch.setenv("NETBOX_MCP_READ_ONLY", "true")
    monkeypatch.setenv("NETBOX_VERIFY_SSL", "false")

    settings = Settings.from_env()

    assert settings.netbox_url == "https://netbox.example.com"
    assert settings.netbox_token == "abc123"
    assert settings.read_only is True
    assert settings.verify_ssl is False


def test_empty_token_treated_as_none(monkeypatch):
    monkeypatch.setenv("NETBOX_TOKEN", "")

    settings = Settings.from_env()

    assert settings.netbox_token is None
