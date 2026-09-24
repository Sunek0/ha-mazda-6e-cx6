"""Tests for the Mazda config and options flows.

The flows are driven directly with a lightweight fake Home Assistant, because
the repository test environment does not ship the full Home Assistant test
framework. The API client is replaced with a fake that records the login calls.
"""

from unittest.mock import AsyncMock, patch

import pytest

from custom_components.mazda_6e_cx6.config_flow import (
    LOGIN_METHOD_EMAIL,
    LOGIN_METHOD_PASSWORD,
    MazdaConfigFlow,
    MazdaOptionsFlow,
    _login_error,
)
from custom_components.mazda_6e_cx6.mazda import (
    AuthToken,
    MazdaAuthError,
    MazdaConnectionError,
    MazdaRateLimitError,
    Vehicle,
)


class _FakeHass:
    """Minimal stand-in for HomeAssistant."""


def _flow(source: str = "user") -> MazdaConfigFlow:
    flow = MazdaConfigFlow()
    flow.hass = _FakeHass()
    flow.context = {"source": source}
    flow.flow_id = "test-flow"
    flow.handler = "mazda_6e_cx6"
    return flow


class _FakeClient:
    """Fake Mazda client recording the login calls."""

    instances: list["_FakeClient"] = []
    error: Exception | None = None

    def __init__(self, **kwargs) -> None:
        self.private_key_pem = "test_private_key"
        self.public_key = "test_public_key"
        self.device_id = kwargs.get("device_id") or "test-device-id"
        self.user_id = "user-1"
        self.email_code_requests: list[str] = []
        self.password_logins: list[tuple[str, str, str | None]] = []
        self.email_code_logins: list[tuple[str, str, str | None]] = []
        self.closed = False
        type(self).instances.append(self)

    async def request_email_code(self, email: str) -> None:
        if self.error is not None:
            raise self.error
        self.email_code_requests.append(email)

    async def login_with_email_password(
        self, email: str, password: str, sales_country: str | None = None
    ) -> AuthToken:
        if self.error is not None:
            raise self.error
        self.password_logins.append((email, password, sales_country))
        return _token()

    async def login_with_email_code(
        self, email: str, code: str, sales_country: str | None = None
    ) -> AuthToken:
        if self.error is not None:
            raise self.error
        self.email_code_logins.append((email, code, sales_country))
        return _token()

    async def get_vehicles(self) -> list[Vehicle]:
        if self.error is not None:
            raise self.error
        return [
            Vehicle(car_id="car-1", vin="TESTVIN0000000001", series_name="Mazda 6e")
        ]

    async def close(self) -> None:
        self.closed = True


def _token() -> AuthToken:
    return AuthToken(
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        cac_token="test_cac_token",
        user_id="user-1",
    )


@pytest.fixture(autouse=True)
def _reset_fake_client():
    _FakeClient.instances = []
    _FakeClient.error = None
    yield
    _FakeClient.instances = []
    _FakeClient.error = None


def _patched_flow(source: str = "user") -> MazdaConfigFlow:
    flow = _flow(source)
    flow.async_set_unique_id = AsyncMock()
    flow._abort_if_unique_id_configured = lambda *args, **kwargs: None
    return flow


@pytest.mark.asyncio
async def test_user_step_offers_password_and_email_code():
    flow = _flow()
    result = await flow.async_step_user()
    schema = result["data_schema"].schema
    assert result["step_id"] == "user"
    login_method = next(key for key in schema if key.schema == "login_method")
    assert login_method.default() == LOGIN_METHOD_PASSWORD
    assert set(schema[login_method].container) == {
        LOGIN_METHOD_PASSWORD,
        LOGIN_METHOD_EMAIL,
    }


@pytest.mark.asyncio
async def test_password_login_creates_entry():
    flow = _patched_flow()
    with patch(
        "custom_components.mazda_6e_cx6.config_flow.MazdaClient", _FakeClient
    ), patch(
        "custom_components.mazda_6e_cx6.config_flow._vehicle_device_entry",
        return_value=None,
    ):
        result = await flow.async_step_email_password(
            {
                "country": "ES",
                "email": "test.user@example.com",
                "password": "secret-password",
            }
        )

    assert result["type"] == "create_entry"
    data = result["data"]
    assert data["access_token"] == "test_access_token"
    assert data["refresh_token"] == "test_refresh_token"
    assert data["cac_token"] == "test_cac_token"
    assert data["private_key"] == "test_private_key"
    assert data["vehicle_id"] == "car-1"
    assert data["email"] == "test.user@example.com"
    assert data["country"] == "ES"
    client = _FakeClient.instances[-1]
    assert client.password_logins == [
        ("test.user@example.com", "secret-password", "ES")
    ]
    assert client.closed is True


@pytest.mark.asyncio
async def test_invalid_credentials_map_to_invalid_auth():
    _FakeClient.error = MazdaAuthError("Authentication failed: bad credentials")
    flow = _patched_flow()
    with patch(
        "custom_components.mazda_6e_cx6.config_flow.MazdaClient", _FakeClient
    ):
        result = await flow.async_step_email_password(
            {
                "country": "ES",
                "email": "test.user@example.com",
                "password": "wrong-password",
            }
        )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "invalid_auth"}


@pytest.mark.asyncio
async def test_email_code_flow_requests_code_and_creates_entry():
    flow = _patched_flow()
    with patch(
        "custom_components.mazda_6e_cx6.config_flow.MazdaClient", _FakeClient
    ):
        request_result = await flow.async_step_intl_email(
            {"country": "ES", "email": "test.user@example.com"}
        )
        assert request_result["step_id"] == "intl_email_code"
        assert _FakeClient.instances[-1].email_code_requests == [
            "test.user@example.com"
        ]

    with patch(
        "custom_components.mazda_6e_cx6.config_flow.MazdaClient", _FakeClient
    ), patch(
        "custom_components.mazda_6e_cx6.config_flow._vehicle_device_entry",
        return_value=None,
    ):
        result = await flow.async_step_intl_email_code({"auth_code": "123456"})

    assert result["type"] == "create_entry"
    assert result["data"]["access_token"] == "test_access_token"
    assert _FakeClient.instances[-1].email_code_logins == [
        ("test.user@example.com", "123456", "ES")
    ]


@pytest.mark.asyncio
async def test_login_without_vehicles_keeps_the_form():
    class _NoVehicleClient(_FakeClient):
        async def get_vehicles(self):
            return []

    flow = _patched_flow()
    with patch(
        "custom_components.mazda_6e_cx6.config_flow.MazdaClient", _NoVehicleClient
    ):
        result = await flow.async_step_email_password(
            {
                "country": "ES",
                "email": "test.user@example.com",
                "password": "secret-password",
            }
        )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "no_vehicles"}


def test_login_error_mapping():
    assert _login_error(MazdaRateLimitError("too many")) == "too_many_codes"
    assert (
        _login_error(MazdaAuthError("CAC_1_1_01_024 not registered"))
        == "account_not_registered"
    )
    assert _login_error(MazdaAuthError("APP_1_1_07_002 bad code")) == "bad_code"
    assert _login_error(MazdaAuthError("rejected")) == "invalid_auth"
    assert _login_error(MazdaConnectionError("offline")) == "cannot_connect"


class _FakeConfigEntries:
    """Config entries registry stub returning one fake entry."""

    def __init__(self, entry):
        self._entry = entry

    def async_get_known_entry(self, entry_id):
        return self._entry


def _options_flow() -> MazdaOptionsFlow:
    entry = type("Entry", (), {"options": {}})()
    flow = MazdaOptionsFlow()
    flow.hass = type("Hass", (), {"config_entries": _FakeConfigEntries(entry)})()
    flow.handler = "test-entry"
    return flow


@pytest.mark.asyncio
async def test_options_flow_exposes_mazda_environments():
    flow = _options_flow()
    result = await flow.async_step_init()
    schema = result["data_schema"].schema
    environment = next(
        value for key, value in schema.items() if key.schema == "environment"
    )
    values = [option["value"] for option in environment.config["options"]]
    assert values == ["prod_eu", "preprod_eu"]


@pytest.mark.asyncio
async def test_options_flow_round_trip():
    flow = _options_flow()
    result = await flow.async_step_init(
        {"scan_interval": 300, "environment": "preprod_eu"}
    )
    assert result["type"] == "create_entry"
    assert result["data"]["scan_interval"] == 300
    assert result["data"]["environment"] == "preprod_eu"
