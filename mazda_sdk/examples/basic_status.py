"""Example: Password login and REST status of a Mazda 6e / CX-6e."""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mazda import MazdaClient


async def main():
    email = os.getenv("MAZDA_EMAIL")
    password = os.getenv("MAZDA_PASSWORD")
    country = os.getenv("MAZDA_COUNTRY", "ES")
    if not email or not password:
        print("Set MAZDA_EMAIL and MAZDA_PASSWORD before running this example.")
        return

    async with MazdaClient(country=country) as client:
        await client.login_with_email_password(email, password)
        print("Login successful.")

        vehicles = await client.get_vehicles()
        if not vehicles:
            print("No vehicles found for this account.")
            return

        for car in vehicles:
            print(f"\n--- Vehicle: {car.series_name} ({car.car_id}) ---")
            print(f"VIN: {car.vin}")
            if car.license_plate:
                print(f"Plate: {car.license_plate}")

            condition = await client.get_vehicle_condition(car.car_id, vin=car.vin)
            print(f"Total Odometer: {condition.total_odometer_km} km")
            print(f"Battery SoC: {condition.battery.soc_percentage}%")
            print(f"Remaining Range: {condition.battery.remaining_range_km} km")
            print(f"Doors Locked: {condition.doors.locked}")
            print(f"AC Active: {condition.climate.power_on}")


if __name__ == "__main__":
    asyncio.run(main())
