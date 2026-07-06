# Bandabou Rain

A tiny Home Assistant custom integration for rain monitoring in Bandabou,
Curacao.

It uses the free Open-Meteo forecast API at the default Soto/Bandabou
coordinates:

- Latitude: `12.267`
- Longitude: `-69.100`

The integration includes local Home Assistant brand assets:

- `custom_components/bandabou_rain/brand/icon.png`
- `custom_components/bandabou_rain/brand/logo.png`

## Important HACS Note

HACS cannot install from private GitHub repositories. To install through HACS,
this repository must be public and added as a custom repository.

## Install With HACS

1. Push this folder to a public GitHub repository.
2. In Home Assistant, open HACS.
3. Open the three-dot menu.
4. Select **Custom repositories**.
5. Paste the GitHub repository URL.
6. Choose category **Integration**.
7. Download **Bandabou Rain**.
8. Restart Home Assistant.
9. Go to **Settings > Devices & services > Add integration**.
10. Search for **Bandabou Rain** and add it.

## What It Creates

- `binary_sensor.bandabou_rain_raining`
- `sensor.bandabou_rain_current_precipitation`
- `sensor.bandabou_rain_rain_next_3_hours`
- `sensor.bandabou_rain_max_rain_probability_next_3_hours`
- `sensor.bandabou_rain_dry_days`
- `weather.bandabou_rain`

The integration can call a Home Assistant notify service when rain starts.
Notification settings are configurable from **Settings > Devices & services >
Bandabou Rain > Configure**.

You can set:

- rain detection threshold
- dry-day threshold
- one or more notify recipients, including `notify.mobile_app_*` phone services
- notification title
- notification message
- notification cooldown
- dry-streak notifications when the location has been dry for a configured
  number of completed days
- dry-streak notification title, message, and cooldown

Notification messages support these placeholders:

```text
{location}
{current_precipitation}
{current_rain}
{current_showers}
{rain_next_3_hours}
{max_rain_probability_next_3_hours}
{dry_days}
{last_rain_date}
{rain_threshold_mm}
{dry_day_threshold_mm}
{dry_streak_threshold_days}
{latitude}
{longitude}
```

## Dashboard

The integration exposes a real Home Assistant weather entity, so you can use
the built-in **Weather Forecast** card:

```yaml
type: weather-forecast
entity: weather.bandabou_rain
name: Bandabou
show_current: true
show_forecast: true
forecast_type: hourly
round_temperature: true
```

For a compact dashboard, paste the example from:

```text
examples/dashboard-weather-stack.yaml
```

For a simple dry-days widget, add a normal **Tile** card for:

```text
sensor.bandabou_rain_dry_days
```

This sensor counts consecutive completed local Curacao days without rain,
ending yesterday. The dry/wet threshold uses the configured rain threshold.

The integration also exposes a 24-hour rain forecast on the current
precipitation sensor's `forecast` attribute. For a rain graph, install
`apexcharts-card` from HACS and add this manual Lovelace card:

```yaml
type: custom:apexcharts-card
graph_span: 24h
header:
  show: true
  title: Bandabou Rain Forecast
  show_states: true
now:
  show: true
  label: Now
yaxis:
  - id: rain
    min: 0
    decimals: 1
    apex_config:
      title:
        text: mm
  - id: probability
    min: 0
    max: 100
    opposite: true
    decimals: 0
    apex_config:
      title:
        text: "%"
series:
  - entity: sensor.bandabou_rain_current_precipitation
    name: Rain
    type: column
    color: "#2f80ed"
    unit: mm
    yaxis_id: rain
    data_generator: |
      const forecast = entity.attributes.forecast || [];
      return forecast.map((point) => [
        Number(point.timestamp) * 1000,
        Number(point.precipitation) || 0
      ]);
  - entity: sensor.bandabou_rain_current_precipitation
    name: Probability
    type: line
    color: "#f2994a"
    unit: "%"
    yaxis_id: probability
    data_generator: |
      const forecast = entity.attributes.forecast || [];
      return forecast.map((point) => [
        Number(point.timestamp) * 1000,
        Number(point.precipitation_probability) || 0
      ]);
```
