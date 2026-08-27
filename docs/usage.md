# Usage Guide

## Quick tour

1. **Register** — open the app, pick *Register*, enter name/email/password
   (min 8 chars). You're logged in immediately.
2. **Add a vehicle** — name, make, model, year, plate, fuel type, current
   odometer. Add up to 10.
3. **Check the schedule** — the dashboard shows overdue services per vehicle;
   the vehicle page lists every maintenance prediction with due km/date and
   a plain-language reason ("Overdue by 1200 km", "Coming up soon…").
4. **Log a service** — after an oil change, tap *Log service*, pick the type,
   enter the odometer + cost. Gaadi bumps the vehicle odometer if the reading
   is higher.
5. **Log fuel** — enter odometer, liters, cost, and mark *full tank* when the
   tank was actually full. Mileage appears after two full-tank fill-ups.
6. **Share the report** — in the vehicle page, toggle *Enable sharing*; copy
   the link and send it to a buyer or mechanic. Anyone with the link sees the
   service history. Toggle off anytime.

## Maintenance intervals

Defaults (override via `MAINTENANCE_INTERVALS` in `.env`):

| Key | Name | km interval | day interval |
|-----|------|-------------|--------------|
| `oil` | Oil Change | 5000 | 90 |
| `tires` | Tire Rotation | 10000 | 180 |
| `brakes` | Brake Inspection | 20000 | 365 |
| `general` | General Service | 10000 | 180 |

Format: `key=Name:km:days` comma-separated, e.g.
`oil=Oil Change:5000:90,tires=Tire Rotation:10000:180`.

## What "overdue" means

A service is overdue when **either** the km interval or the day interval has
passed since the last record of that type. A vehicle with no records at all
baselines from creation — so it only becomes overdue once the first interval
passes.

## Fuel mileage notes

- Mileage is only calculated between **consecutive full-tank** fill-ups.
- Partial fill-ups (unticked) still count toward totals and cost.
- `cost_per_km` = total fuel cost over the full-tank span ÷ distance driven.

## API keys / tokens

No API keys needed — auth is JWT per user. The public share endpoint is the
only unauthenticated route, and it requires the (unguessable) share token
plus `share_enabled=true`.
