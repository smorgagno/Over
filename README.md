# Over

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Over is an [AppDaemon](https://appdaemon.readthedocs.io/) app for [Home Assistant](https://www.home-assistant.io/).

It watches Shelly diagnostic binary sensors (`overheating`, `overpowering`, and `overvoltage`) and sends a notification when a device goes into protection.

Over does **not** read temperature, power, or voltage on its own. Home Assistant already exposes those events. This app listens for `on`, waits out a per-sensor cooldown, and then calls your `notify` services.

## How it works

1. In `apps.yaml`, list the `binary_sensor` entities in `over_sensors`.
2. On startup and on every AppDaemon reload, the app listens with `new="on"` and `immediate=True`. If a sensor is already `on`, you get a notification right away.
3. An `off` state does **not** send a notification unless you set `notify_on_clear: true`.
4. `unavailable` and `unknown` are ignored because the listener only matches `on`.
5. `notification_interval` is a cooldown **per sensor**. An alert on one device does not hide an alert on another device.

## Install with HACS

HACS copies the `apps/Over/` folder (the Python file and `translations/`). It does not edit `apps.yaml` for you.

1. Install [HACS](https://hacs.xyz/) and the **AppDaemon** add-on.
2. In HACS, open the menu (three dots) and choose **Custom repositories**.
3. Add `https://github.com/smorgagno/Over` with category **AppDaemon**.
4. Search for **Over** and install it.
5. Copy the sample block from [`examples/apps.yaml`](examples/apps.yaml) into AppDaemon `apps/apps.yaml`. Replace the sample entity IDs with yours.
6. Restart AppDaemon, or reload apps.

After each [GitHub release](https://github.com/smorgagno/Over/releases), use **Update** in HACS. New optional YAML keys can wait; the app uses defaults if they are missing.

[Open this repository in HACS](https://my.home-assistant.io/redirect/hacs_repository/?owner=smorgagno&repository=Over&category=appdaemon)

## Install by hand

1. Install the **AppDaemon** add-on and connect it to Home Assistant.
2. Copy this repository's `apps/Over/` folder into AppDaemon `apps`.
3. Add the `Over:` block from [`examples/apps.yaml`](examples/apps.yaml) to `apps/apps.yaml`.
4. Restart AppDaemon. The log should show how many sensors are being watched.

```text
addon_configs/..._appdaemon/
  apps/
    apps.yaml
    Over/
      Over.py
      translations/
        en.json
        it.json
```

You need Shelly binary sensors (`*_overheating`, `*_overpowering`, `*_overvoltage`) and at least one Home Assistant notify service, such as Telegram.

## Configuration

```yaml
Over:
  module: Over
  class: Over
  language: en
  notify_on_clear: false
  over_sensors:
    - binary_sensor.device_overheating
    - binary_sensor.device_overpowering
    - binary_sensor.device_overvoltage
  notification_services:
    - telegram
  notification_interval: 120
```

| Key | Required | Default | What it does |
|---|---|---|---|
| `module` / `class` | yes | — | Must both be `Over` |
| `over_sensors` | yes | — | Binary sensors to watch |
| `notification_services` | yes | — | Notify service names (`telegram` becomes `notify/telegram`) |
| `notification_interval` | no | `60` | Seconds to wait before the **same** sensor can notify again |
| `language` | no | `en` | Translation file to load from `translations/` |
| `notify_on_clear` | no | `false` | Also notify when the sensor goes back to `off` |

If an entity is missing in Home Assistant, Over logs it and keeps running.

## Languages

Built-in files:

- `translations/en.json` — English (default, always loaded as fallback)
- `translations/it.json` — Italian

Set `language` to the file name without `.json`. Example: `language: it`.

Missing keys in another language fall back to English.

### Add a language

1. Copy `translations/en.json` to `translations/<code>.json` (for example `de.json`).
2. Translate the **values** only. Keep the keys and `{name}` / `{entity}` / `{count}` / `{language}` placeholders.
3. Set `language: de` (or your code) in `apps.yaml`.
4. Reload the app.

A pull request with a new `translations/<code>.json` file is welcome.

## Version notes

This release targets AppDaemon 4.5 (`from appdaemon.plugins.hass import Hass`). Compared with 1.x, Over no longer notifies on `off` or `unknown`, and the cooldown is per sensor instead of global.
