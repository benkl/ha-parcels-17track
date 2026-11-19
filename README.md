# Parcels for 17TRACK

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/docs/faq/custom_repositories)
[![Validate](https://github.com/benkl/ha-parcels-17track/actions/workflows/validate.yml/badge.svg)](https://github.com/benkl/ha-parcels-17track/actions/workflows/validate.yml)

A parcel overview for Home Assistant built on the official
[17TRACK integration](https://www.home-assistant.io/integrations/seventeentrack/).
It adds a dashboard card, push notifications, an add-parcel form and automatic archiving.

## Features

- **Dashboard card** with the status icon, latest event, location and "x hours ago" for each parcel. Parcels that need attention are listed first (problems, out for delivery, ready for pickup), delivered parcels are folded away, and you can add parcels right from the card. The card loads by itself, so you don't need to add a resource.
- **"Out for delivery" detection** from the latest tracking event, using keywords you can change. 17TRACK itself only reports "in transit".
- **Push notifications** for new parcels, parcels on their way or out for delivery today, ready for pickup, delivered, and problems. They work with any `notify.*` service, and on the mobile app tapping one opens the parcel in 17TRACK.
- **Change events** (`parcels_17track_changed`) for your own automations.
- **Auto-archive** of delivered parcels after a number of days you choose.
- **Sensors**: open parcels (with the full parcel list as an attribute), in transit, out for delivery, ready for pickup, delivered, problems, last update, plus a **Delivery today** binary sensor.
- **Services** `parcels_17track.add_parcel`, `archive_parcel` and `refresh`. These also work for non-admin users.
- Parcel states are remembered across restarts, so you never get duplicate notifications and don't miss any.
- English and German.

## Installation

1. Set up the built-in **17TRACK** integration (Settings → Devices & services → Add integration → 17TRACK).
2. In HACS: ⋮ → **Custom repositories** → add `https://github.com/benkl/ha-parcels-17track` as type **Integration**.
3. Install **Parcels for 17TRACK** and restart Home Assistant.
4. Settings → Devices & services → Add integration → **Parcels for 17TRACK**, then pick your 17TRACK account.

## Settings

Settings → Devices & services → Parcels for 17TRACK → **Configure**:

| Option | Default | |
|---|---|---|
| Refresh interval | 30 min | How often 17TRACK is polled. |
| Send notifications to | – | Any notify services, e.g. `notify.mobile_app_pixel`. |
| Notify about | everything | New, on its way, out for delivery, ready for pickup, delivered, problem. |
| Archive delivered parcels after | 3 days | Runs daily at 04:00. `0` turns it off. |
| "Out for delivery" keywords | EN/DE/FR/IT/ES/NL | Comma separated. They're matched against the latest tracking event. |

## Dashboard card

Add the card from the card picker (**17TRACK Parcels**), or in YAML:

```yaml
type: custom:parcels-17track-card
entity: sensor.17track_parcels_open_parcels
title: Pakete          # optional
show_delivered: true   # optional
show_add_form: true    # optional
```

## Automation example

```yaml
triggers:
  - trigger: event
    event_type: parcels_17track_changed
    event_data:
      type: ready_for_pickup
actions:
  - action: tts.speak
    target:
      entity_id: tts.home_assistant_cloud
    data:
      media_player_entity_id: media_player.kitchen
      message: "{{ trigger.event.data.name }} is ready for pickup."
```

Event data: `type` (`new`, `in_transit`, `out_for_delivery`, `ready_for_pickup`, `delivered`, `problem`), `state`, `previous_state`, `tracking_number`, `name`, `info_text`, `location`, `url`.

## Notes

- This is not an official 17TRACK product. It relies on the account access of the built-in Home Assistant integration.
- The full parcel list attribute is excluded from the recorder, so it doesn't fill your database.
