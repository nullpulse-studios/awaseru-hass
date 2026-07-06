# Bandabou Rain

A tiny Home Assistant custom integration for rain monitoring in Bandabou,
Curacao.

It uses the free Open-Meteo forecast API at the default Soto/Bandabou
coordinates:

- Latitude: `12.267`
- Longitude: `-69.100`

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

The integration can call a Home Assistant notify service when rain starts.
The default is:

```text
notify.notify
```

If you want a specific phone, use your mobile app notify service instead, for
example:

```text
notify.mobile_app_your_phone
```

## Dashboard Graph

The integration exposes a 24-hour forecast on the current precipitation
sensor's `forecast` attribute. For a future rain graph, install
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
