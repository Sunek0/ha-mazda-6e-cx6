"""API endpoints and base URLs for the Mazda CMA gateway.

Paths are relative to the gateway prefix for REST calls and include the full
path for the CA/MQTT host, matching the routes recovered from the Mazda
6e & CX-6e 1.2.3 app (see ``docs/apk-mazda-1.2.3.md``).
"""

from dataclasses import dataclass

# Base hostnames
MAZDA_EU_BASE_URL = "https://cma-m.iov.changanauto.com.de"
MAZDA_EU_CA_BASE_URL = "https://ca-m.iov.changanauto.com.de"
MAZDA_EU_PREPROD_BASE_URL = "https://cma-m-uat.iov.changanauto.com.de"
MAZDA_EU_PREPROD_CA_BASE_URL = "https://ca-m-uat.iov.changanauto.com.de"

MAZDA_APP_ID = "com.cma.mazda.eu"


@dataclass(frozen=True)
class MazdaEnvironment:
    """Regional gateway definition recovered from the app's MazdaEnvBean."""

    id: str
    label: str
    app_id: str
    base_url: str
    ca_base_url: str
    gateway_prefix: str = "/cma-app-gw/cma-app-gw"


MAZDA_ENVIRONMENTS: dict[str, MazdaEnvironment] = {
    environment.id: environment
    for environment in (
        MazdaEnvironment(
            "prod_eu",
            "Europe",
            MAZDA_APP_ID,
            MAZDA_EU_BASE_URL,
            MAZDA_EU_CA_BASE_URL,
        ),
        MazdaEnvironment(
            "preprod_eu",
            "Europe preproduction",
            MAZDA_APP_ID,
            MAZDA_EU_PREPROD_BASE_URL,
            MAZDA_EU_PREPROD_CA_BASE_URL,
        ),
    )
}
DEFAULT_MAZDA_ENVIRONMENT = "prod_eu"


def get_mazda_environment(environment: str) -> MazdaEnvironment:
    """Return the environment definition or raise for an unknown identifier."""
    try:
        return MAZDA_ENVIRONMENTS[environment]
    except KeyError as exc:
        supported = ", ".join(sorted(MAZDA_ENVIRONMENTS))
        raise ValueError(
            f"Unknown Mazda environment {environment!r}; supported: {supported}."
        ) from exc


# Authentication endpoints (cma-app-auth)
MAZDA_SEND_EMAIL_CODE = "/cma-app-gw/cma-app-auth/api/login/email-send-auth-code"
MAZDA_LOGIN_BY_EMAIL_CODE = "/cma-app-gw/cma-app-auth/api/login/email-code-in"
MAZDA_LOGIN_BY_EMAIL_CODE_V2 = "/cma-app-gw/cma-app-auth/api/login/email-code-in/v2"
MAZDA_LOGIN_BY_EMAIL_PASSWORD = "/cma-app-gw/cma-app-auth/api/login/email-pass-in"
MAZDA_LOGIN_BY_EMAIL_PASSWORD_V2 = "/cma-app-gw/cma-app-auth/api/login/email-pass-in/v2"
MAZDA_LOGOUT = "/cma-app-gw/cma-app-auth/api/logout"
MAZDA_REFRESH_TOKEN = "/cma-app-gw/cma-app-auth/api/auth/refresh-token"

# Vehicle endpoints (cma-app-user / cma-app-car-condition)
MAZDA_GET_MY_CARS = "/cma-app-gw/cma-app-user/api/car/vehicles"
# Only the v2 condition route exists in the Mazda app.
MAZDA_GET_VEHICLE_CONDITION = "/cma-app-gw/cma-app-car-condition/api/vehicle/condition/v2"
# Per-vehicle function configuration (CarApi.getCarConfig in the app DEX)
MAZDA_GET_FUNCTION_CONFIG = "/cma-app-gw/cma-app-user/api/vehicle/function-config"

# Control endpoints (cma-app-car-control)
MAZDA_GET_SERIAL_NO = "/cma-app-gw/cma-app-car-control/api/serial-no/get"
MAZDA_CHECK_CONTROL_CODE = "/cma-app-gw/cma-app-car-control/api/security-code/check-code"
MAZDA_GET_SECURITY_CODE_STATUS = "/cma-app-gw/cma-app-car-control/api/security-code/get-status"
MAZDA_CONTROL_AIR_CONDITIONER = "/cma-app-gw/cma-app-car-control/api/control/air-conditioner"
MAZDA_CONDITION_INQUIRY = "/cma-app-gw/cma-app-car-control/api/control/condition-inquiry"
MAZDA_CONTROL_RESULT = "/cma-app-gw/cma-app-car-control/api/control/control-result"
MAZDA_CONTROL_DOORS = "/cma-app-gw/cma-app-car-control/api/control/doors"
MAZDA_CONTROL_WINDOWS = "/cma-app-gw/cma-app-car-control/api/control/windows"
MAZDA_CONTROL_TRUNK = "/cma-app-gw/cma-app-car-control/api/control/trunk"
MAZDA_CONTROL_FLASHING_HONKING = (
    "/cma-app-car-control/api/control/flashing-honking"
)
MAZDA_CHARGE_PERCENTAGE = "/cma-app-gw/cma-app-car-control/api/charge/percentage"
MAZDA_CHARGE_MODIFY_PLAN = "/cma-app-gw/cma-app-car-control/api/charge/modify-plan"
MAZDA_CHARGE_ADD_PLAN = "/cma-app-gw/cma-app-car-control/api/charge/add-plan"
MAZDA_CHARGE_DELETE_PLAN = "/cma-app-gw/cma-app-car-control/api/charge/delete-plan"
MAZDA_CHARGE_VALIDITY = "/cma-app-gw/cma-app-car-control/api/charge/validity"
MAZDA_CONTROL_DEFROST = "/cma-app-gw/cma-app-car-control/api/control/defrost"
MAZDA_CONTROL_SEATS_HEAT = "/cma-app-gw/cma-app-car-control/api/control/seats/heat"
MAZDA_CONTROL_SEATS_WIND = "/cma-app-gw/cma-app-car-control/api/control/seats/wind"
MAZDA_CONTROL_STEERING_WHEEL_HEAT = (
    "/cma-app-car-control/api/control/steering-wheel/heat"
)
MAZDA_CONTROL_FOTA_PLAN = "/cma-app-gw/cma-app-car-control/api/control/fota-plan"
MAZDA_DEPARTURE_ADD_PLAN = (
    "/cma-app-car-control/api/departure-plans/add-plan"
)
MAZDA_DEPARTURE_MODIFY_PLAN = (
    "/cma-app-car-control/api/departure-plans/modify-plan"
)
MAZDA_DEPARTURE_DELETE = "/cma-app-gw/cma-app-car-control/api/departure-plans/delete"
MAZDA_DEPARTURE_VALIDITY = (
    "/cma-app-car-control/api/departure-plans/validity"
)
MAZDA_DEPARTURE_ENABLED = (
    "/cma-app-car-control/api/departure-plans/enabled"
)

# CA gateway (MQTT telemetry bootstrap)
MAZDA_CA_GET_CONN_CONF = "/user-apigw/vot-connect-conf-center/api/device/getConnConf"
MAZDA_CA_GET_AUTH_TOKEN = "/user-apigw/vot-connect-auth-center/api/auth/getAuthTokenByUserId"
# App fallback recovered from the Mazda app DEX (MqttConstansKt)
MAZDA_CA_GET_CAR_CONF_FUNC = (
    "/user-apigw/vot-connect-conf-center/api/device/appGetCarConfFunc"
)

REQUEST_ENCRYPTION_PUBLIC_KEY = (
    "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAkyhr43cBPTJ3jLiYsmbUwUp74cMJIOju5vqVzgtuK63Q99qV6iVT8wN5cXlyMtWI2mfOmhIao/fUN821im69MfOHsWXdqQEo5e9v654GPw+bju0pCphEPtD1I0VcyS34QkAu04urSun2U1q3Dr2OICLVWSnLa+01ioKxkaB0D209zXcls2eFQpvRAWm7xxVsoqzSwqp+neu5quOpn+eO/bW0TxcSQ8VZcDEUvadRTLSR0eOWgRuHIBiD2RGqPIPzKCm5A14q1qhxUZ8U0pmYe0Sx7eMy4RVe2iW7fnjc6pxTUMBkercSL26mevYouuCKqyie+LVQAtGa29RMl/lyiwIDAQAB"
)
