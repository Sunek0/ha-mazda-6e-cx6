"""Entity availability tests for the Mazda integration platforms.

The platform builders are called with a lightweight fake coordinator, so the
tests assert which entities a vehicle gains or loses without starting Home
Assistant.
"""

from custom_components.mazda_6e_cx6.binary_sensor import build_binary_sensors
from custom_components.mazda_6e_cx6.mazda import (
    MazdaClient,
    Vehicle,
    VehicleCapabilities,
)
from custom_components.mazda_6e_cx6.number import build_control_numbers
from custom_components.mazda_6e_cx6.sensor import build_sensors
from custom_components.mazda_6e_cx6.vehicle_model import (
    is_bev,
    seat_supported,
    supports_fuel,
)

VEHICLE = Vehicle(car_id="car-1", vin="TESTVIN0000000001", series_name="Mazda 6e")
BEV_VEHICLE = Vehicle(
    car_id="car-2", vin="TESTVIN0000000002", series_name="Mazda 6e BEV"
)


def _coordinator(capabilities):
    class _Coordinator:
        data: dict = {}
        client = MazdaClient(device_id="test-device-id")

        def vehicle_capabilities(self, car_id):
            return capabilities

        def vehicle_uses_mqtt(self, car_id):
            return False

    return _Coordinator()


def _seat_sensors(entities):
    return {
        (entity._position, entity._kind)
        for entity in entities
        if type(entity).__name__ == "MazdaSeatLevelSensor"
    }


def _translation_keys(entities):
    return {
        getattr(entity, "_attr_translation_key", None) for entity in entities
    }


def test_rear_seat_entities_follow_capabilities():
    capabilities = VehicleCapabilities.from_codes(
        ["#driverSeatHeat", "#passengerSeatHeat", "#driverSeatVent"]
    )
    coordinator = _coordinator(capabilities)

    seats = _seat_sensors(build_sensors(coordinator, VEHICLE))
    assert ("front_left", "heating_level") in seats
    assert ("front_right", "heating_level") in seats
    assert ("front_left", "ventilation_level") in seats
    assert ("rear_left", "heating_level") not in seats
    assert ("rear_right", "heating_level") not in seats

    binary_keys = _translation_keys(build_binary_sensors(coordinator, VEHICLE))
    assert "front_left_seat_heating" in binary_keys
    assert "rear_left_seat_heating" not in binary_keys
    assert "rear_right_seat_heating" not in binary_keys


def test_unknown_capabilities_keep_the_seat_entities():
    coordinator = _coordinator(None)
    seats = _seat_sensors(build_sensors(coordinator, VEHICLE))
    assert ("rear_left", "heating_level") in seats
    assert ("rear_right", "heating_level") in seats
    assert seat_supported(None, "rear_left", "heating") is None


def test_fuel_sensors_only_for_fuel_vehicles():
    fuel_capabilities = VehicleCapabilities.from_codes(["#oilMileage"])
    assert supports_fuel(VEHICLE, fuel_capabilities) is True
    assert supports_fuel(BEV_VEHICLE, fuel_capabilities) is False
    assert is_bev(BEV_VEHICLE) is True

    fuel_sensors = _translation_keys(
        build_sensors(_coordinator(fuel_capabilities), VEHICLE)
    )
    assert "fuel_level" in fuel_sensors

    no_fuel_sensors = _translation_keys(
        build_sensors(_coordinator(VehicleCapabilities.from_codes([])), VEHICLE)
    )
    assert "fuel_level" not in no_fuel_sensors


def test_charge_limit_number_is_created_for_command_capable_vehicles():
    numbers = build_control_numbers(_coordinator(None), VEHICLE)
    assert any(type(number).__name__ == "MazdaChargeLimitNumber" for number in numbers)
