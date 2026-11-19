# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [1.0.1] – 2026-11-20

### Added
- Brand icon (`brand/icon.png`, `icon@2x.png`) so Home Assistant and HACS show the integration's own icon.
- Manifest `categories` (`productivity_information`) and `connectivity` (`cloud`).

## [1.0.0] – 2026-11-20

### Added
- Config flow linking a 17TRACK account set up with the core integration.
- Options for refresh interval, notify targets, notify events, auto-archive days and out-for-delivery keywords.
- Sensors: open parcels (with the parcel list), in transit, out for delivery, ready for pickup, delivered, problems, last update. Binary sensor: delivery today.
- Services `add_parcel`, `archive_parcel`, `refresh`, usable by non-admin users.
- `parcels_17track_changed` event and push notifications, with parcel states remembered across restarts.
- Bundled `custom:parcels-17track-card` with a visual editor and an add-parcel form.
- English and German translations, plus diagnostics with personal data left out.
- HACS README with banner, card and notification previews, full reference, automation examples and FAQ.
- Issue templates, Dependabot for GitHub Actions, and CI (hassfest, HACS validation, tests).

[1.0.1]: https://github.com/benkl/ha-parcels-17track/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/benkl/ha-parcels-17track/releases/tag/v1.0.0
