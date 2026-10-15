"""Route shapes of the Mazda CMA gateway constants.

Regression guard for the 1.2.3 APK reverification
(``docs/apk-mazda-1.2.3-rea-reverification.md``): every REST route must carry
the ``/cma-app-gw`` prefix the app's Retrofit annotations use, the CA routes
the ``/user-apigw`` host path, and no route may repeat the gateway prefix.
"""

from mazda import endpoints


def _route_constants():
    for name in dir(endpoints):
        if not name.startswith("MAZDA_"):
            continue
        value = getattr(endpoints, name)
        if isinstance(value, str) and value.startswith("/"):
            yield name, value


def test_every_route_carries_its_gateway_prefix():
    for name, path in _route_constants():
        if path.startswith("/user-apigw/"):
            continue
        assert path.startswith("/cma-app-gw/cma-app-"), (name, path)


def test_no_route_repeats_the_gateway_prefix():
    for name, path in _route_constants():
        assert "/cma-app-gw/cma-app-gw" not in path, (name, path)


def test_environment_gateway_prefix_is_not_duplicated():
    for environment in endpoints.MAZDA_ENVIRONMENTS.values():
        assert environment.gateway_prefix == "/cma-app-gw"


def test_control_routes_match_the_app_paths():
    """The routes that lost the gateway prefix before the reverification."""
    assert (
        endpoints.MAZDA_CONTROL_FLASHING_HONKING
        == "/cma-app-gw/cma-app-car-control/api/control/flashing-honking"
    )
    assert (
        endpoints.MAZDA_CONTROL_STEERING_WHEEL_HEAT
        == "/cma-app-gw/cma-app-car-control/api/control/steering-wheel/heat"
    )
    assert (
        endpoints.MAZDA_DEPARTURE_ADD_PLAN
        == "/cma-app-gw/cma-app-car-control/api/departure-plans/add-plan"
    )
    assert (
        endpoints.MAZDA_DEPARTURE_MODIFY_PLAN
        == "/cma-app-gw/cma-app-car-control/api/departure-plans/modify-plan"
    )
    assert (
        endpoints.MAZDA_DEPARTURE_VALIDITY
        == "/cma-app-gw/cma-app-car-control/api/departure-plans/validity"
    )
    assert (
        endpoints.MAZDA_DEPARTURE_ENABLED
        == "/cma-app-gw/cma-app-car-control/api/departure-plans/enabled"
    )
