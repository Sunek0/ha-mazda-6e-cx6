"""Sensor platform for Mazda integration."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfLength,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DEFAULT_MODEL,
    DENSITY_MICROGRAMS_PER_CUBIC_METER,
    DOMAIN,
    MANUFACTURER,
)
from .coordinator import MazdaDataUpdateCoordinator
from .mazda import MazdaClient
from .runtime_data import MazdaConfigEntry
from .vehicle_model import seat_supported, supports_fuel

# Coordinator is used to centralize the data updates
PARALLEL_UPDATES = 0


# Fuel sensors exist only for fuel vehicles (see supports_fuel).
FUEL_SENSOR_KEYS = frozenset({"fuel_level", "fuel_range", "fuel_tank_capacity"})

def build_sensors(
    coordinator: MazdaDataUpdateCoordinator, vehicle: Any
) -> list[SensorEntity]:
    """Build the sensors for one vehicle, skipping what its capabilities lack."""
    entities: list[SensorEntity] = [
        MazdaBatterySocSensor(coordinator, vehicle),
        MazdaRemainingRangeSensor(coordinator, vehicle),
        MazdaOdometerSensor(coordinator, vehicle),
    ]

    if coordinator.vehicle_uses_mqtt(vehicle.car_id):
        entities.extend([
            MazdaMileageYesterdaySensor(coordinator, vehicle),
            MazdaTripMileageSensor(coordinator, vehicle),
        ])

    if isinstance(coordinator.client, MazdaClient):
        capabilities = coordinator.vehicle_capabilities(vehicle.car_id)

        for key in ("front_left", "front_right", "rear_left", "rear_right"):
            entities.append(MazdaTirePressureSensor(coordinator, vehicle, key))

        for position in ("front_left", "front_right", "rear_left", "rear_right"):
            if seat_supported(capabilities, position, "heating") is False:
                continue
            entities.append(
                MazdaSeatLevelSensor(coordinator, vehicle, position, "heating_level")
            )
        for position in ("front_left", "front_right"):
            if seat_supported(capabilities, position, "ventilation") is False:
                continue
            entities.append(
                MazdaSeatLevelSensor(coordinator, vehicle, position, "ventilation_level")
            )

        entities.append(MazdaSteeringWheelHeaterLevelSensor(coordinator, vehicle))

        fuel = supports_fuel(vehicle, capabilities)

        entities.extend(
            MazdaSensor(coordinator, vehicle, description)
            for description in SENSORS
            if not (description.key in FUEL_SENSOR_KEYS and not fuel)
        )

    return entities

async def async_setup_entry(
    hass: HomeAssistant,
    entry: MazdaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mazda sensors based on a config entry."""
    coordinator: MazdaDataUpdateCoordinator = entry.runtime_data.coordinator

    entities: list[SensorEntity] = []

    for vehicle in coordinator.vehicles:
        entities.extend(build_sensors(coordinator, vehicle))

    async_add_entities(entities)

class MazdaBaseSensor(CoordinatorEntity[MazdaDataUpdateCoordinator], SensorEntity):
    """Base class for Mazda sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: MazdaDataUpdateCoordinator, vehicle: Any) -> None:
        """Initialize base sensor."""
        super().__init__(coordinator)
        self.vehicle = vehicle
        self._car_id = vehicle.car_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for Home Assistant."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.vehicle.car_id)},
            name=self.vehicle.series_name or DEFAULT_MODEL,
            manufacturer=MANUFACTURER,
            model=self.vehicle.series_name or DEFAULT_MODEL,
        )

class MazdaBatterySocSensor(MazdaBaseSensor):
    """Battery State of Charge (%) sensor."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:car-battery"

    def __init__(self, coordinator: MazdaDataUpdateCoordinator, vehicle: Any) -> None:
        super().__init__(coordinator, vehicle)
        self._attr_unique_id = f"mazda_{vehicle.car_id}_battery_soc"
        self._attr_translation_key = "battery_level"

    @property
    def native_value(self) -> int | None:
        """Return battery SoC %."""
        cond = self.coordinator.data.get(self._car_id)
        return cond.battery.soc_percentage if cond else None

class MazdaRemainingRangeSensor(MazdaBaseSensor):
    """Remaining range (km) sensor."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_icon = "mdi:gauge"

    def __init__(self, coordinator: MazdaDataUpdateCoordinator, vehicle: Any) -> None:
        super().__init__(coordinator, vehicle)
        self._attr_unique_id = f"mazda_{vehicle.car_id}_remaining_range"
        self._attr_translation_key = "remaining_range"

    @property
    def native_value(self) -> int | None:
        """Return estimated range in km."""
        cond = self.coordinator.data.get(self._car_id)
        return cond.battery.remaining_range_km if cond else None

class MazdaOdometerSensor(MazdaBaseSensor):
    """Total mileage / odometer (km) sensor."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_icon = "mdi:counter"

    def __init__(self, coordinator: MazdaDataUpdateCoordinator, vehicle: Any) -> None:
        super().__init__(coordinator, vehicle)
        self._attr_unique_id = f"mazda_{vehicle.car_id}_total_odometer"
        self._attr_translation_key = "total_odometer"

    @property
    def native_value(self) -> float | None:
        """Return the total odometer in km."""
        cond = self.coordinator.data.get(self._car_id)
        return cond.total_odometer_km if cond else None

class MazdaMileageYesterdaySensor(MazdaBaseSensor):
    """Mileage driven yesterday (km) sensor, MQTT-backed vehicles only."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator: MazdaDataUpdateCoordinator, vehicle: Any) -> None:
        super().__init__(coordinator, vehicle)
        self._attr_unique_id = f"mazda_{vehicle.car_id}_mileage_yesterday"
        self._attr_translation_key = "mileage_yesterday"

    @property
    def native_value(self) -> float | None:
        """Return yesterday's mileage in km."""
        cond = self.coordinator.data.get(self._car_id)
        return cond.mileage_yesterday_km if cond else None

class MazdaTripMileageSensor(MazdaBaseSensor):
    """Mileage since the current ignition cycle (km), MQTT-backed vehicles only."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_icon = "mdi:map-marker-path"

    def __init__(self, coordinator: MazdaDataUpdateCoordinator, vehicle: Any) -> None:
        super().__init__(coordinator, vehicle)
        self._attr_unique_id = f"mazda_{vehicle.car_id}_trip_mileage"
        self._attr_translation_key = "trip_mileage"

    @property
    def native_value(self) -> float | None:
        """Return the trip mileage in km."""
        cond = self.coordinator.data.get(self._car_id)
        return cond.trip_mileage_km if cond else None

class MazdaTirePressureSensor(MazdaBaseSensor):
    """Tire pressure (bar) sensor for international vehicles."""

    _attr_device_class = SensorDeviceClass.PRESSURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "bar"
    _attr_icon = "mdi:tire"

    def __init__(self, coordinator: MazdaDataUpdateCoordinator, vehicle: Any, key: str) -> None:
        super().__init__(coordinator, vehicle)
        self._key = key
        self._attr_unique_id = f"mazda_{vehicle.car_id}_tire_{key}_pressure"
        self._attr_translation_key = f"tire_pressure_{key}"

    @property
    def native_value(self) -> float | None:
        """Return tire pressure in bar."""
        cond = self.coordinator.data.get(self._car_id)
        if not cond:
            return None
        return getattr(cond.tires, self._key).pressure_bar

class MazdaSeatLevelSensor(MazdaBaseSensor):
    """Seat heating or ventilation level sensor for international vehicles."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:car-seat"

    def __init__(
        self,
        coordinator: MazdaDataUpdateCoordinator,
        vehicle: Any,
        position: str,
        kind: str,
    ) -> None:
        super().__init__(coordinator, vehicle)
        self._position = position
        self._kind = kind
        self._attr_unique_id = f"mazda_{vehicle.car_id}_seat_{position}_{kind}"
        self._attr_translation_key = f"seat_{kind}_{position}"

    @property
    def native_value(self) -> int | None:
        """Return the seat level."""
        cond = self.coordinator.data.get(self._car_id)
        if not cond:
            return None
        return getattr(getattr(cond.seats, self._position), self._kind)

class MazdaSteeringWheelHeaterLevelSensor(MazdaBaseSensor):
    """Steering wheel heater level sensor for international vehicles."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:steering"

    def __init__(self, coordinator: MazdaDataUpdateCoordinator, vehicle: Any) -> None:
        super().__init__(coordinator, vehicle)
        self._attr_unique_id = f"mazda_{vehicle.car_id}_steering_wheel_heater_level"
        self._attr_translation_key = "steering_wheel_heater_level"

    @property
    def native_value(self) -> int | None:
        """Return the steering wheel heater level."""
        cond = self.coordinator.data.get(self._car_id)
        return cond.climate.steering_wheel_heater_level if cond else None

@dataclass(frozen=True, kw_only=True)
class MazdaSensorDescription(SensorEntityDescription):
    """Description of an extended international sensor."""

    value_fn: Callable[[Any, Any], Any]

SENSORS: tuple[MazdaSensorDescription, ...] = (
    MazdaSensorDescription(
        key="speed",
        name="Speed",
        value_fn=lambda cond, vehicle: cond.speed_kmh,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        icon="mdi:speedometer",
    ),
    MazdaSensorDescription(
        key="inside_temperature",
        name="Inside Temperature",
        value_fn=lambda cond, vehicle: cond.climate.inside_temperature_c,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        icon="mdi:thermometer",
    ),
    MazdaSensorDescription(
        key="outside_temperature",
        name="Outside Temperature",
        value_fn=lambda cond, vehicle: cond.climate.outside_temperature_c,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        icon="mdi:thermometer-lines",
    ),
    MazdaSensorDescription(
        key="cabin_humidity",
        name="Cabin Humidity",
        value_fn=lambda cond, vehicle: cond.climate.humidity,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:water-percent",
    ),
    MazdaSensorDescription(
        key="inside_pm25",
        name="Inside PM2.5",
        value_fn=lambda cond, vehicle: cond.climate.inside_pm25,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=DENSITY_MICROGRAMS_PER_CUBIC_METER,
        icon="mdi:blur",
    ),
    MazdaSensorDescription(
        key="air_quality_level",
        name="Air Quality Level",
        value_fn=lambda cond, vehicle: cond.climate.air_quality_level,
        device_class=None,
        state_class=None,
        native_unit_of_measurement=None,
        icon="mdi:air-filter",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    MazdaSensorDescription(
        key="charge_status",
        name="Charge Status",
        value_fn=lambda cond, vehicle: cond.battery.charging_status,
        device_class=None,
        state_class=None,
        native_unit_of_measurement=None,
        icon="mdi:battery-charging",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    MazdaSensorDescription(
        key="charge_current",
        name="Charge Current",
        value_fn=lambda cond, vehicle: cond.battery.charge_current_a,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        icon="mdi:current-ac",
    ),
    MazdaSensorDescription(
        key="ac_charge_current",
        name="AC Charge Current",
        value_fn=lambda cond, vehicle: cond.battery.ac_charge_current_a,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        icon="mdi:current-ac",
    ),
    MazdaSensorDescription(
        key="dc_charge_current",
        name="DC Charge Current",
        value_fn=lambda cond, vehicle: cond.battery.dc_charge_current_a,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        icon="mdi:current-dc",
    ),
    MazdaSensorDescription(
        key="remaining_charge_time",
        name="Remaining Charge Time",
        value_fn=lambda cond, vehicle: cond.battery.remaining_charge_time_min,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:timer-sand",
    ),
    MazdaSensorDescription(
        key="charge_limit",
        name="Charge Limit",
        value_fn=lambda cond, vehicle: cond.battery.charge_limit_percent,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:battery-lock",
    ),
    MazdaSensorDescription(
        key="charge_schedule_start",
        name="Charge Schedule Start",
        value_fn=lambda cond, vehicle: cond.battery.charge_schedule_start,
        device_class=None,
        state_class=None,
        native_unit_of_measurement=None,
        icon="mdi:clock-start",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    MazdaSensorDescription(
        key="charge_schedule_end",
        name="Charge Schedule End",
        value_fn=lambda cond, vehicle: cond.battery.charge_schedule_end,
        device_class=None,
        state_class=None,
        native_unit_of_measurement=None,
        icon="mdi:clock-end",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    MazdaSensorDescription(
        key="fuel_level",
        name="Fuel Level",
        value_fn=lambda cond, vehicle: cond.fuel.level_percent,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:gas-station",
    ),
    MazdaSensorDescription(
        key="fuel_range",
        name="Fuel Range",
        value_fn=lambda cond, vehicle: cond.fuel.remaining_range_km,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        icon="mdi:gas-station-outline",
    ),
    MazdaSensorDescription(
        key="fuel_tank_capacity",
        name="Fuel Tank Capacity",
        value_fn=lambda cond, vehicle: cond.fuel.tank_capacity_l,
        device_class=SensorDeviceClass.VOLUME,
        state_class=None,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        icon="mdi:fuel",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    MazdaSensorDescription(
        key="vehicle_status",
        name="Vehicle Status",
        value_fn=lambda cond, vehicle: cond.vehicle_status,
        device_class=None,
        state_class=None,
        native_unit_of_measurement=None,
        icon="mdi:car-info",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    MazdaSensorDescription(
        key="power_status",
        name="Power Status",
        value_fn=lambda cond, vehicle: cond.power_status,
        device_class=None,
        state_class=None,
        native_unit_of_measurement=None,
        icon="mdi:power",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    MazdaSensorDescription(
        key="gear",
        name="Gear",
        value_fn=lambda cond, vehicle: cond.gear,
        device_class=None,
        state_class=None,
        native_unit_of_measurement=None,
        icon="mdi:car-shift-pattern",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    MazdaSensorDescription(
        key="epb_status",
        name="Electronic Parking Brake",
        value_fn=lambda cond, vehicle: cond.epb_status,
        device_class=None,
        state_class=None,
        native_unit_of_measurement=None,
        icon="mdi:car-brake-parking",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    MazdaSensorDescription(
        key="last_updated",
        name="Last Updated",
        value_fn=lambda cond, vehicle: (
            datetime.fromtimestamp(cond.last_updated_timestamp, tz=UTC)
            if cond.last_updated_timestamp is not None
            else None
        ),
        device_class=SensorDeviceClass.TIMESTAMP,
        state_class=None,
        native_unit_of_measurement=None,
        icon="mdi:clock-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)

class MazdaSensor(MazdaBaseSensor):
    """Extended international sensor driven by a description."""

    entity_description: MazdaSensorDescription

    def __init__(
        self,
        coordinator: MazdaDataUpdateCoordinator,
        vehicle: Any,
        description: MazdaSensorDescription,
    ) -> None:
        super().__init__(coordinator, vehicle)
        self.entity_description = description
        self._attr_unique_id = f"mazda_{vehicle.car_id}_{description.key}"
        self._attr_translation_key = description.key
        if description.device_class is not None:
            self._attr_device_class = description.device_class
        if description.state_class is not None:
            self._attr_state_class = description.state_class
        if description.native_unit_of_measurement is not None:
            self._attr_native_unit_of_measurement = (
                description.native_unit_of_measurement
            )
        if description.icon is not None:
            self._attr_icon = description.icon
        if description.entity_category is not None:
            self._attr_entity_category = description.entity_category

    @property
    def native_value(self) -> Any:
        """Return the described value."""
        cond = self.coordinator.data.get(self._car_id)
        if not cond:
            return None
        return self.entity_description.value_fn(cond, self.vehicle)
