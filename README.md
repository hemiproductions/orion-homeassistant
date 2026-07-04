# Orion for Home Assistant

A native [Home Assistant](https://www.home-assistant.io/) integration for
Orion, the TV/movie/game tracker. Installable via [HACS](https://hacs.xyz/) —
no YAML required.

Talks to your Orion instance's token-authed `/api/machine/*` HTTP API
(see `docs/home-assistant.md` in the Orion repo for the endpoint contract).

## Features

- **Sensors** (one poll of `/api/machine/summary` per interval feeds all of them):
  - `sensor.orion_up_next` — the next unwatched aired episode across your followed shows
  - `sensor.orion_airing_today` / `sensor.orion_airing_week` — counts + item lists
  - `sensor.orion_unwatched_episodes` — total unwatched-but-aired count
  - `sensor.orion_releasing_soon` — followed items releasing today/tomorrow
- **`button.orion_sync`** — trigger an immediate catalog refresh + notification check
- **Services** — write back to Orion from automations or scripts:
  - `orion.mark_watched` — mark an episode/movie/game watched or unwatched
  - `orion.set_followed` — follow/unfollow a show/movie/game, archive/unarchive a show

## Installation

### Via HACS (recommended)

1. HACS → Integrations → ⋮ → Custom repositories → add
   `https://github.com/hemiproductions/orion-homeassistant` as an **Integration**.
2. Install "Orion", restart Home Assistant.
3. **Settings → Devices & Services → Add Integration → Orion.**
4. Enter your Orion instance URL (e.g. `https://orionmedia.app` or
   `http://dev.orionmedia.app`) and the API token shown on Orion's Settings page.

### Manual

Copy `custom_components/orion` into your Home Assistant config's
`custom_components/` directory and restart.

## Configuration

All setup happens through the config flow UI (URL + token). Polling interval
(default 15 minutes) can be changed afterward via the integration's
**Configure** option.

## Notes

- Requires Orion's `/api/machine/summary`, `/api/machine/watched`,
  `/api/machine/follow`, and `/api/machine/sync` endpoints (added alongside
  this integration — update Orion if those 404).
- For instant "new release" pushes (rather than polling), you can still point
  Orion's `WEBHOOK_URL` at an HA webhook automation; see Orion's
  `docs/home-assistant.md` for that YAML. The native integration and the
  webhook push are complementary, not exclusive.
