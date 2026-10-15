# ha-mazda-6e-cx6

Home Assistant custom integration for **Mazda 6e** and **Mazda CX-6e** connected vehicles over the official Mazda app backend (`com.cma.mazda.eu`).

## Important warnings

- Unofficial project, not affiliated with Mazda or Changan Automobile. Use it at your own risk.
- Remote commands act on the real vehicle. Make sure it is safe before using locks, windows, trunk,
  climate, lights or horn.
- It cannot drive the car: the BLE/digital-key path is not implemented.
- The Mazda gateway has not been verified with a real account and vehicle yet (see
  **Troubleshooting**). Treat the integration as experimental until that happens.
- Signing in with an account can sign that account out of the official Mazda app, and signing in to
  the app again can invalidate the Home Assistant session. Use a **secondary account** shared from
  your main account to avoid this (see below).

## Supported vehicles

The integration talks to the Mazda CMA gateway the MAZDA 6e & CX-6e app uses.

| Model | Notes |
| --- | --- |
| Mazda 6e (Deepal L07 twin) | Telemetry and signed remote controls through the REST API; MQTT telemetry when the API reports `protocolType: MQTT`. |
| Mazda CX-6e (Deepal S07 twin) | Telemetry and signed remote controls through the REST API; MQTT telemetry when the API reports `protocolType: MQTT`. |

Vehicles whose API reports `protocolType: MQTT` report telemetry through the CA/MQTT gateway and
stay read-only unless you enable the experimental remote controls option; the rest use the signed
REST command flow. Controls also depend on what each car and account allow. For a model not listed
here, telemetry and the generic vehicle image still work.

## Recommended setup: use a secondary account

Logging in to Home Assistant with your main Mazda app account can sign it out of your phone. The
recommended setup is to create a second account, share the vehicle from the main account and use the
secondary account only for Home Assistant:

1. In the Mazda app, create a new account with a different email and note its credentials.
2. Still signed in with your **main** account, open the vehicle, tap **Share** and invite the new
   account.
3. Sign in to the app with the **new** account and accept the shared vehicle control.
4. If you want to control the doors, windows or trunk, create the control PIN with the new account:
   try to lower the windows from the app, it asks you to create a PIN, create it and check that the
   command works. Those commands are signed with the PIN and require it; climate, lights and horn do
   not need it.
5. Sign out of the app and add the integration in Home Assistant with the **new** account. Your main
   account can stay signed in on the phone.

## Requirements

- Home Assistant 2026.3.0 or newer, matching the `homeassistant` baseline in `hacs.json`
  (Python 3.13+; Home Assistant 2026.9 uses Python 3.14).
- A Mazda app account (`com.cma.mazda.eu`) with at least one 6e or CX-6e linked. The HACS metadata
  advertises the countries with a translated language: Spain, Portugal, the United Kingdom, Ireland,
  France, Belgium, Luxembourg, Germany, Austria, Switzerland, Italy and Greece.

## Installation

### HACS

1. In HACS, add this repository as a custom repository of type **Integration**:
   `https://github.com/Sunek0/ha-mazda-6e-cx6`.
2. Install **Mazda 6e & CX-6e** and restart Home Assistant.
3. Add the integration from **Settings > Devices & services** and sign in with the account email and
   password, or request an email verification code.

Updating keeps the same `mazda_6e_cx6` domain, so no reconfiguration is needed.

### Manual

1. Copy `custom_components/mazda_6e_cx6/` into your Home Assistant `config/custom_components/`
   directory.
2. Restart Home Assistant and add the integration as described above.

## Configuration

Open **Settings > Devices & services > Mazda 6e & CX-6e > Configure** to change these options:

- **Enable experimental remote controls for MQTT vehicles**: required to control climate, lights and
  horn on vehicles that report over MQTT. Without it, those vehicles stay read-only.
- **Remote control PIN**: required for the door lock, window and trunk commands. Use the PIN created
  with the account Home Assistant signs in with (the secondary one); a PIN created with another
  account is rejected.
- **Scan interval**, **API logging**, **regional environment** and **declared Android version**:
  polling cadence and troubleshooting helpers. Leave the defaults unless you are debugging.

## Supported features

### Authentication and session

- Email and password login, with the email verification code flow as an alternative, automatic token
  refresh and a reauthentication flow.
- The account vehicle list is re-checked at most every ten minutes, so a vehicle added to or
  removed from the account appears (or disappears) without reloading the entry by hand.
- Integration options for the scan interval, API logging, the regional environment and the declared
  Android version.

### Telemetry

- REST telemetry: battery and range, charging state and currents, remaining charge time, charge
  limit, charge schedule and plan, doors, windows, climate, seats, tires and lamps.
- MQTT telemetry for MQTT-backed vehicles through the CA gateway, including the mileage fields.
- Fuel telemetry on PHEV/range-extender vehicles (fuel level, fuel range and tank capacity); the
  entities are only created when the vehicle reports the fuel capability and its model is not a
  BEV, so electric vehicles keep their entity set minimal.
- One Home Assistant device per vehicle, with translated entity names.

### Remote controls

- Signed REST commands: climate, door lock, windows, trunk, charge limit, charge schedule, departure
  plans, lights and horn.
- Comfort commands: seat heating and ventilation levels and steering-wheel heating.
- The door lock, window and trunk commands require the remote control PIN created with the account
  Home Assistant signs in with; their entities are only created once the PIN is saved in the
  integration options.

### Vehicle image

- One image entity per vehicle: the API picture when it loads, and a bundled per-model placeholder
  (Mazda 6e, Mazda CX-6e or a generic Mazda image) served instantly otherwise, so the device page
  always shows a picture even when the API image is slow or missing.

### Diagnostics

- Redacted diagnostics download with the mapped telemetry, the raw payloads, the unmapped MQTT keys
  and the per-vehicle capability codes reported by the app backend.

## Troubleshooting

- **"Authentication failed"**: check the email and password, or request a new verification code.
  Repeated failures can rate-limit the account; wait before retrying.
- **Rate limited by the gateway**: the integration defers the next refresh using the gateway's
  `Retry-After` when it is provided, and never polls sooner than the configured scan interval.
- **No entities**: the account may have no vehicle linked, or the vehicle reports a model the
  integration does not know; telemetry and the generic image still work.
- **"Remote control PIN is not set" although a PIN is configured in Home Assistant**: the PIN was
  not created in the account Home Assistant uses. Sign in to the app with that account, create the
  PIN (step 4 above) and save it again in the integration options.
- **Home Assistant asks to reauthenticate**: the session was invalidated from the app or another
  device. Sign in again; using the secondary account avoids most of these.
- **Values look stale**: the vehicle only reports telemetry while it is awake; the integration shows
  the last known snapshot until the car reports again.
- **Commands rejected**: the control PIN must be created with the account used by Home Assistant.
- **MQTT vehicles read-only**: enable the experimental MQTT controls option.
- **Fuel entities are missing on a PHEV**: the integration creates them only when the vehicle's
  function configuration reports `#oilMileage` and the model is not a BEV. Check `capabilities` in
  the diagnostics.
- **A telemetry field is missing**: download the diagnostics from the device page and check
  `unmapped_mqtt_keys`; enable debug logging for `mazda_sdk` to see the candidate values in the
  Home Assistant log. Credentials, VIN and location-like values are redacted in the report.
- **Login, telemetry or commands fail with gateway errors**: the Mazda gateway behaviour is still
  pending live verification. Enable **Log redacted API traffic**, reproduce the failure and report
  it with the redacted log.

## Disclaimer

Unofficial project, not affiliated with Mazda or Changan Automobile. Use it at your own risk.
