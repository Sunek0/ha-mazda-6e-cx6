"""Runtime data for the Mazda 6e & CX-6e integration."""

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry

from .coordinator import MazdaDataUpdateCoordinator
from .mazda import MazdaClient


@dataclass
class MazdaRuntimeData:
    """Objects shared by the Mazda entity platforms."""

    client: MazdaClient
    coordinator: MazdaDataUpdateCoordinator


type MazdaConfigEntry = ConfigEntry[MazdaRuntimeData]
