# Mazda Python SDK

SDK asíncrono para la API de telemática y control remoto de los vehículos **Mazda 6e y CX-6e**
(equivalentes a los Changan Deepal L07 y S07). Habla con el gateway CMA que usa la app
**MAZDA 6e & CX-6e** (`com.cma.mazda.eu`, versión 1.2.3), no con el gateway internacional de
My Changan.

Este paquete es independiente de `deepal_sdk`: no lo importa y no comparte estado con él.

## Características

- ⚡ **Asíncrono:** construido sobre `httpx` y `asyncio`.
- 🔐 **Autenticación:** login por correo con código de verificación o con contraseña
  (`cma-app-auth`), con el cifrado RSA que usa la app, refresco de sesión y logout.
- 🚗 **Telemática:** lista de vehículos, configuración de funciones y condición (batería y carga,
  autonomía, odómetro, puertas, ventanillas, climatización, asientos, neumáticos y combustible en
  PHEV).
- 📡 **MQTT:** bootstrap CA (`getConnConf`, `appGetCarConfFunc`, `getAuthTokenByUserId`) y
  instantánea de condición en vivo.
- 🎛️ **Control remoto:** comandos firmados (clima, puertas, ventanillas, maletero, aviso
  luces/claxon, planes de carga y salida) con PIN de control.
- 📐 **Tipado estricto:** modelos validados con Pydantic v2.

> Aviso: el protocolo se ha recuperado del APK 1.2.3 (`docs/apk-mazda-1.2.3.md`). Las partes que
> dependen del gateway (`cma-app-gw`) están pendientes de validación con una cuenta Mazda real; ver
> `docs/mazda-api.md`.

## Instalación

```bash
pip install -e .
```

Los ejemplos de `examples/` se pueden ejecutar directamente con cualquier intérprete que tenga las
dependencias del SDK, sin necesidad de instalarlo antes:

```bash
python mazda_sdk/examples/basic_status.py
```

## Entornos

| Identificador | REST | CA/MQTT |
| --- | --- | --- |
| `prod_eu` (por defecto) | `https://cma-m.iov.changanauto.com.de/cma-app-gw` | `https://ca-m.iov.changanauto.com.de/user-apigw` |
| `preprod_eu` | `https://cma-m-uat.iov.changanauto.com.de/cma-app-gw` | `https://ca-m-uat.iov.changanauto.com.de/user-apigw` |

El SDK se identifica con `appid: com.cma.mazda.eu` y `appversion: V1.2.0` (valores del entorno de
producción UE de `MazdaEnvBean`).

## Login por contraseña

```python
import asyncio
from mazda import MazdaClient

async def main():
    async with MazdaClient(country="ES") as client:
        await client.login_with_email_password("tu-correo@ejemplo.com", "tu-contraseña")
        vehicles = await client.get_vehicles()
        for car in vehicles:
            cond = await client.get_vehicle_condition(car.car_id, vin=car.vin)
            print(f"{car.series_name}: {cond.battery.soc_percentage}% | {cond.total_odometer_km} km")

asyncio.run(main())
```

La app también expone rutas `/v2` para el login; el SDK las usa con `use_v2=True`.

## Login por código de correo

```python
import asyncio
from mazda import MazdaClient

async def main():
    async with MazdaClient(country="ES") as client:
        await client.request_email_code("tu-correo@ejemplo.com")
        code = input("Código recibido por correo: ")
        token = await client.login_with_email_code("tu-correo@ejemplo.com", code)
        print(f"Access Token: {token.access_token}")

asyncio.run(main())
```

Ejemplo ejecutable: `python mazda_sdk/examples/email_login_example.py`.

## Telemetría MQTT

```python
import asyncio
from mazda import MazdaClient

async def main():
    async with MazdaClient(country="ES") as client:
        await client.login_with_email_password("tu-correo@ejemplo.com", "tu-contraseña")
        car = (await client.get_vehicles())[0]
        if client.is_mqtt_vehicle(car):
            cond = await client.mqtt_condition(car.car_id, vin=car.vin)
            print(cond.battery.soc_percentage, cond.doors.locked)

asyncio.run(main())
```

Ejemplo ejecutable: `python mazda_sdk/examples/mqtt_status.py`.

## Control remoto

```python
await client.check_control_code("1234")           # PIN de control
await client.control_air_conditioner("CAR_ID", enabled=True, target_temp_c=22.0)
await client.control_doors("CAR_ID", open_value=False)
result = await client.control_result_status("CAR_ID", command_id)
```

## Estructura del Proyecto

- `mazda/client.py`: cliente asíncrono principal (`MazdaClient`).
- `mazda/models/`: modelos Pydantic (`Vehicle`, `VehicleCondition`, `AuthToken`, ...).
- `mazda/endpoints.py`: entornos y endpoints del gateway CMA.
- `mazda/mqtt.py`: transporte MQTT 5.0 y normalización de parámetros.
- `examples/`: scripts de demostración.
