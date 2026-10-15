# Mazda API reference

Surface implemented by `mazda_sdk`, recovered from the **MAZDA 6e & CX-6e 1.2.3** app
(`com.cma.mazda.eu`). Everything marked *unverified* comes from static analysis (the app method
bodies are VMP-extracted) and must be confirmed with a real Mazda account.

## Environments

| Environment | REST (`baseUrl`) | CA/MQTT (`mqttUrl`) | appId | appVersion |
| --- | --- | --- | --- | --- |
| `prod_eu` (default) | `https://cma-m.iov.changanauto.com.de/cma-app-gw/` | `https://ca-m.iov.changanauto.com.de/user-apigw/` | `com.cma.mazda.eu` | `V1.2.0` |
| `preprod_eu` | `https://cma-m-uat.iov.changanauto.com.de/cma-app-gw/` | `https://ca-m-uat.iov.changanauto.com.de/user-apigw/` | `com.cma.mazda.eu` | — |

The app also defines `prod_g_new` and `preprod_g_new` (ASEAN, `com.cma.mazda.sg`), out of scope for
now.

## Headers

| Header | Value |
| --- | --- |
| `appid` | `com.cma.mazda.eu` |
| `appversion` | `V1.2.0` |
| `language`, `apptype`, `devicetype`, `deviceid`, `selectcountry` | same as the app |
| `x-os-version` | `9` (*unverified*: the Mazda DEX has no literal; sent by parity with the verified Changan flow) |
| `authorization` | `<accessToken>\|<cacToken>` |
| `X-Tsp-User-Token`, `X-VCS-User-Token` | access token |

The exported app does not carry `X-Tsp-Timestamp`, `X-VCS-Timestamp`, `X-VCS-Nonce`, `X-Pkg-Id` nor
`X-VCS-Hu-Token`.

## Authentication (`cma-app-auth`)

`POST` with JSON; sensitive values are RSA-encrypted with the app public key (the same key the
Changan app uses).

| Operation | Path | Body |
| --- | --- | --- |
| Send email code | `/cma-app-gw/cma-app-auth/api/login/email-send-auth-code` | `{type:"0", email}` |
| Login with code | `/cma-app-gw/cma-app-auth/api/login/email-code-in[/v2]` | `{authCode, salesCountry, email, pubKey}` |
| Login with password | `/cma-app-gw/cma-app-auth/api/login/email-pass-in[/v2]` | `{salesCountry, email, password, pubKey}` (*unverified body*) |
| Refresh | `/cma-app-gw/cma-app-auth/api/auth/refresh-token` | `{}` |
| Logout | `/cma-app-gw/cma-app-auth/api/logout` | `{}` |

Login response (`UserEntity`): `token`, `refreshToken`, `cacToken`, `userId`, `caUserId`,
`cacUserId`, `hwId`, `controlToken`, `caControlToken`.

## Vehicles and telemetry

| Operation | Path | Body |
| --- | --- | --- |
| Vehicle list | `/cma-app-gw/cma-app-user/api/car/vehicles` | `{}` |
| Function configuration | `/cma-app-gw/cma-app-user/api/vehicle/function-config` | `{carId}` candidates (*unverified*) |
| Condition | `/cma-app-gw/cma-app-car-condition/api/vehicle/condition/v2` | `{vechileCriteria:{...}, vehicleId}` |

`vechileCriteria` (same typo as the app): `seat`, `door`, `hvac`, `charge`, `lamp`, `window`,
`tire`, `vehicleStatus`, `fuel`. Only the v2 condition route exists in the Mazda app; its response
shape is assumed to match the Changan v1 block names and the parser is tolerant.

## CA and MQTT

| Operation | Path (CA host) | Body |
| --- | --- | --- |
| MQTT config | `/user-apigw/vot-connect-conf-center/api/device/getConnConf` | `{deviceId, carId, deviceType:1, confTimestamp:0, deviceTimestamp}` |
| MQTT config (fallback) | `/user-apigw/vot-connect-conf-center/api/device/appGetCarConfFunc` | same |
| MQTT token | `/user-apigw/vot-connect-auth-center/api/auth/getAuthTokenByUserId` | `{userId}` |

The broker, topics, `secretKey` and AES-CBC encryption are the same shared code the Changan app
uses. A Mazda account has not been verified against the CA gateway yet.

## Remote control (`cma-app-car-control`)

Serial number (`serial-no/get`), control PIN (`security-code/check-code`, `security-code/get-status`)
and signed commands: `control/air-conditioner`, `control/doors`, `control/windows`, `control/trunk`,
`control/flashing-honking`, `control/defrost`, `control/seats/heat`, `control/seats/wind`,
`control/steering-wheel/heat`, `control/fota-plan`, `control/condition-inquiry`,
`control/control-result`, `charge/{percentage,modify-plan,add-plan,delete-plan,validity}` and
`departure-plans/{add-plan,modify-plan,delete,validity,enabled}`.

## Digital key (not implemented)

The app manages the BLE key through `cma-app-user/api/digital-key/mix/*` and
`/app2/api/dk/key/*`. It is out of scope for this SDK.

## Pending verification

1. Which headers `cma-app-gw` accepts.
2. The exact `condition/v2` and `function-config` response shapes.
3. That the CA gateway accepts a Mazda account access token as `X-Tsp-User-Token`.
4. The exact password-login and signed-command bodies.
