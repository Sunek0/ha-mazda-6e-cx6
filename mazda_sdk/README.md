# Mazda Python SDK

Async SDK for the telemetry and remote-control API of the **Mazda 6e and CX-6e** vehicles (the
Changan Deepal L07 and S07 twins). It talks to the CMA gateway the **MAZDA 6e & CX-6e** app uses
(`com.cma.mazda.eu`, version 1.2.3), not to the My Changan international gateway.

This package is independent from `deepal_sdk`: it does not import it and shares no state with it.

## Features

- ⚡ **Async:** built on `httpx` and `asyncio`.
- 🔐 **Authentication:** email login with a verification code or password (`cma-app-auth`), with the
  RSA encryption the app uses, session refresh and logout.
- 🚗 **Telemetry:** vehicle list, function configuration and condition (battery and charge, range,
  odometer, doors, windows, climate, seats, tires and fuel on PHEVs).
- 📡 **MQTT:** CA bootstrap (`getConnConf`, `appGetCarConfFunc`, `getAuthTokenByUserId`) and live
  condition snapshots; the account auth token is reused within a one-minute window.
- 🎛️ **Remote control:** signed commands (climate, doors, windows, trunk, lights/horn, charge and
  departure plans) with the control PIN.
- 🚦 **Rate limits:** HTTP 429 responses raise a typed rate-limit error carrying the gateway's
  `Retry-After` value.
- 📐 **Strict typing:** models validated with Pydantic v2.

> Warning: the protocol was recovered from the 1.2.3 APK. The parts that depend on the
> `cma-app-gw` gateway are pending validation with a real Mazda account; see [`docs/api.md`](docs/api.md).

## Installation

```bash
pip install -e .
```

The scripts under `examples/` run directly with any interpreter that has the SDK runtime
dependencies, without installing it first:

```bash
python mazda_sdk/examples/basic_status.py
```

## Environments

| Identifier | REST | CA/MQTT |
| --- | --- | --- |
| `prod_eu` (default) | `https://cma-m.iov.changanauto.com.de/cma-app-gw` | `https://ca-m.iov.changanauto.com.de/user-apigw` |
| `preprod_eu` | `https://cma-m-uat.iov.changanauto.com.de/cma-app-gw` | `https://ca-m-uat.iov.changanauto.com.de/user-apigw` |

The SDK identifies itself with `appid: com.cma.mazda.eu` and `appversion: V1.2.0` (the EU
production values from `MazdaEnvBean`).

## Password login

```python
import asyncio
from mazda import MazdaClient

async def main():
    async with MazdaClient(country="ES") as client:
        await client.login_with_email_password("your-email@example.com", "your-password")
        vehicles = await client.get_vehicles()
        for car in vehicles:
            cond = await client.get_vehicle_condition(car.car_id, vin=car.vin)
            print(f"{car.series_name}: {cond.battery.soc_percentage}% | {cond.total_odometer_km} km")

asyncio.run(main())
```

The app also exposes `/v2` login routes; the SDK uses them with `use_v2=True`.

## Email code login

```python
import asyncio
from mazda import MazdaClient

async def main():
    async with MazdaClient(country="ES") as client:
        await client.request_email_code("your-email@example.com")
        code = input("Verification code received by email: ")
        token = await client.login_with_email_code("your-email@example.com", code)
        print(f"Access Token: {token.access_token}")

asyncio.run(main())
```

Runnable example: `python mazda_sdk/examples/email_login_example.py`.

## MQTT telemetry

```python
import asyncio
from mazda import MazdaClient

async def main():
    async with MazdaClient(country="ES") as client:
        await client.login_with_email_password("your-email@example.com", "your-password")
        car = (await client.get_vehicles())[0]
        if client.is_mqtt_vehicle(car):
            cond = await client.mqtt_condition(car.car_id, vin=car.vin)
            print(cond.battery.soc_percentage, cond.doors.locked)

asyncio.run(main())
```

Runnable example: `python mazda_sdk/examples/mqtt_status.py`.

## Remote control

```python
await client.check_control_code("1234")           # control PIN
await client.control_air_conditioner("CAR_ID", enabled=True, target_temp_c=22.0)
await client.control_doors("CAR_ID", open_value=False)
result = await client.control_result_status("CAR_ID", command_id)
```

## Project layout

- `mazda/client.py`: main async client (`MazdaClient`).
- `mazda/models/`: Pydantic models (`Vehicle`, `VehicleCondition`, `AuthToken`, ...).
- `mazda/endpoints.py`: CMA gateway environments and endpoints.
- `mazda/mqtt.py`: MQTT 5.0 transport and parameter normalization.
- `examples/`: demonstration scripts.
