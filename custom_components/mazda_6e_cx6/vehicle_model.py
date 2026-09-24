"""Vehicle model helpers shared by the Home Assistant entity platforms."""

from typing import Any


def normalize_model(*values: str | None) -> str:
    """Upper-case alphanumerics of the given model fields, for containment checks."""
    return " ".join(
        "".join(
            character for character in (value or "").upper() if character.isalnum()
        )
        for value in values
    ).strip()


def is_bev(vehicle: Any) -> bool:
    """Return whether the vehicle is battery electric (BEV token in its model)."""
    model = normalize_model(
        vehicle.series_name,
        vehicle.series_code,
        vehicle.model_name,
        vehicle.model_code,
    )
    return "BEV" in model


def supports_fuel(vehicle: Any, capabilities: Any) -> bool:
    """Return whether the vehicle has a fuel tank the fuel entities should expose.

    The app requests the fuel section for every vehicle, so the gate is built
    from the function configuration (`#oilMileage`) plus a BEV model exclusion:
    a PHEV reports the code and a BEV carries the `BEV` token, so both known
    drivetrains resolve without knowing the PHEV model code. Missing
    capabilities or model data keeps the fuel entities away.
    """
    if capabilities is None or not getattr(capabilities, "has_fuel", False):
        return False
    return not is_bev(vehicle)


def seat_supported(
    capabilities: Any, position: str, kind: str
) -> bool | None:
    """Return whether a seat position supports heating or ventilation.

    ``None`` means the capabilities are unknown (the function configuration was
    not fetched), in which case callers keep the entity so a transient failure
    does not hide it. ``False`` means the vehicle explicitly does not declare
    the function and the entity must not be created.
    """
    if capabilities is None:
        return None
    seat = (getattr(capabilities, "seats", None) or {}).get(position)
    if seat is None:
        return None
    return bool(getattr(seat, kind, False))
