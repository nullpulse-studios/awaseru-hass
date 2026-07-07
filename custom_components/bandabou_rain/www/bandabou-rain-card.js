class BandabouRainCard extends HTMLElement {
  setConfig(config) {
    if (!config.entity) {
      throw new Error("Bandabou Rain Card requires an entity");
    }

    this._config = {
      title: "Bandabou Rain",
      hours_to_show: 24,
      dry_days_entity: "sensor.bandabou_rain_dry_days",
      rain_next_3_hours_entity: "sensor.bandabou_rain_rain_next_3_hours",
      probability_entity: "sensor.bandabou_rain_max_rain_probability_next_3_hours",
      ...config,
    };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 4;
  }

  static getStubConfig() {
    return {
      entity: "sensor.bandabou_rain_current_precipitation",
      dry_days_entity: "sensor.bandabou_rain_dry_days",
      rain_next_3_hours_entity: "sensor.bandabou_rain_rain_next_3_hours",
      probability_entity: "sensor.bandabou_rain_max_rain_probability_next_3_hours",
      hours_to_show: 24,
    };
  }

  _render() {
    if (!this._hass || !this._config) {
      return;
    }

    const entity = this._hass.states[this._config.entity];
    const title = escapeHtml(this._config.title || entity?.attributes?.friendly_name || "Bandabou Rain");
    const forecast = getForecastPoints(entity, Number(this._config.hours_to_show) || 24);
    const currentRain = formatEntityState(this._hass, this._config.entity, "mm");
    const nextRain = formatEntityState(this._hass, this._config.rain_next_3_hours_entity, "mm");
    const probability = formatEntityState(this._hass, this._config.probability_entity, "%");
    const dryDays = formatEntityState(this._hass, this._config.dry_days_entity, "d");
    const summary = buildSummary(forecast);
    const icon = summary.totalRain > 0 ? "mdi:weather-pouring" : "mdi:weather-partly-cloudy";

    this.innerHTML = `
      <ha-card>
        <style>
          .card-content {
            padding: 16px;
          }

          .header {
            align-items: center;
            display: flex;
            gap: 12px;
            justify-content: space-between;
            margin-bottom: 14px;
          }

          .title {
            color: var(--primary-text-color);
            font-size: 20px;
            font-weight: 500;
            line-height: 1.25;
          }

          .subtitle {
            color: var(--secondary-text-color);
            font-size: 13px;
            line-height: 1.4;
            margin-top: 2px;
          }

          ha-icon {
            color: var(--state-icon-color);
            flex: 0 0 auto;
            height: 32px;
            width: 32px;
          }

          .stats {
            display: grid;
            gap: 8px;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            margin-bottom: 12px;
          }

          .stat {
            border: 1px solid var(--divider-color);
            border-radius: var(--ha-card-border-radius, 12px);
            min-width: 0;
            padding: 10px 8px;
          }

          .stat-value {
            color: var(--primary-text-color);
            font-size: 18px;
            font-weight: 500;
            line-height: 1.2;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }

          .stat-label {
            color: var(--secondary-text-color);
            font-size: 12px;
            line-height: 1.3;
            margin-top: 4px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }

          .chart {
            border-top: 1px solid var(--divider-color);
            padding-top: 12px;
          }

          svg {
            display: block;
            height: auto;
            max-width: 100%;
            overflow: visible;
            width: 100%;
          }

          .legend {
            align-items: center;
            color: var(--secondary-text-color);
            display: flex;
            flex-wrap: wrap;
            font-size: 12px;
            gap: 12px;
            margin-top: 8px;
          }

          .legend-item {
            align-items: center;
            display: inline-flex;
            gap: 6px;
            min-width: 0;
          }

          .swatch {
            border-radius: 999px;
            display: inline-block;
            height: 8px;
            width: 18px;
          }

          .rain {
            background: var(--info-color, #03a9f4);
          }

          .chance {
            background: var(--warning-color, #ff9800);
          }

          .empty {
            color: var(--secondary-text-color);
            padding: 24px 0 8px;
            text-align: center;
          }

          @media (max-width: 520px) {
            .stats {
              grid-template-columns: repeat(2, minmax(0, 1fr));
            }
          }
        </style>
        <div class="card-content">
          <div class="header">
            <div>
              <div class="title">${title}</div>
              <div class="subtitle">${escapeHtml(summary.label)}</div>
            </div>
            <ha-icon icon="${icon}"></ha-icon>
          </div>
          <div class="stats">
            ${stat("Now", currentRain)}
            ${stat("Next 3h", nextRain)}
            ${stat("Chance", probability)}
            ${stat("Dry days", dryDays)}
          </div>
          <div class="chart">
            ${forecast.length ? renderChart(forecast, this._hass) : '<div class="empty">Forecast data is not available yet.</div>'}
          </div>
          <div class="legend">
            <span class="legend-item"><span class="swatch rain"></span>Rain mm</span>
            <span class="legend-item"><span class="swatch chance"></span>Rain chance</span>
          </div>
        </div>
      </ha-card>
    `;
  }
}

function stat(label, value) {
  return `
    <div class="stat">
      <div class="stat-value">${escapeHtml(value)}</div>
      <div class="stat-label">${escapeHtml(label)}</div>
    </div>
  `;
}

function getForecastPoints(entity, hoursToShow) {
  const forecast = entity?.attributes?.forecast;
  if (!Array.isArray(forecast)) {
    return [];
  }

  const now = Date.now();
  return forecast
    .map((point) => {
      const timestamp = Number(point.timestamp) * 1000 || Date.parse(point.datetime);
      return {
        timestamp,
        precipitation: Math.max(0, Number(point.precipitation) || 0),
        probability: Math.max(0, Math.min(100, Number(point.precipitation_probability) || 0)),
      };
    })
    .filter((point) => Number.isFinite(point.timestamp) && point.timestamp >= now - 60 * 60 * 1000)
    .slice(0, Math.max(1, hoursToShow));
}

function buildSummary(points) {
  if (!points.length) {
    return { label: "Waiting for forecast data", totalRain: 0 };
  }

  const totalRain = points.reduce((sum, point) => sum + point.precipitation, 0);
  const maxChance = Math.max(...points.map((point) => point.probability));
  return {
    totalRain,
    label: `${formatNumber(totalRain, 1)} mm forecast, ${formatNumber(maxChance, 0)}% max chance`,
  };
}

function renderChart(points, hass) {
  const width = 640;
  const height = 220;
  const left = 38;
  const right = 18;
  const top = 16;
  const bottom = 34;
  const chartWidth = width - left - right;
  const chartHeight = height - top - bottom;
  const maxRain = Math.max(1, ...points.map((point) => point.precipitation));
  const count = points.length;
  const barStep = chartWidth / Math.max(1, count);
  const barWidth = Math.max(3, Math.min(18, barStep * 0.55));
  const rainColor = "var(--info-color, #03a9f4)";
  const chanceColor = "var(--warning-color, #ff9800)";
  const gridColor = "var(--divider-color)";
  const textColor = "var(--secondary-text-color)";

  const xFor = (index) =>
    count === 1 ? left + chartWidth / 2 : left + (index / (count - 1)) * chartWidth;
  const rainY = (value) => top + chartHeight - (value / maxRain) * chartHeight;
  const chanceY = (value) => top + chartHeight - (value / 100) * chartHeight;

  const bars = points
    .map((point, index) => {
      const x = xFor(index) - barWidth / 2;
      const y = rainY(point.precipitation);
      const barHeight = Math.max(0, top + chartHeight - y);
      return `<rect x="${round(x)}" y="${round(y)}" width="${round(barWidth)}" height="${round(barHeight)}" rx="2" fill="${rainColor}"></rect>`;
    })
    .join("");

  const line = points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${round(xFor(index))} ${round(chanceY(point.probability))}`)
    .join(" ");

  const dots = points
    .filter((_, index) => index % Math.ceil(count / 8) === 0 || index === count - 1)
    .map((point, index) => {
      const actualIndex = points.indexOf(point);
      return `<circle cx="${round(xFor(actualIndex))}" cy="${round(chanceY(point.probability))}" r="2.5" fill="${chanceColor}"></circle>`;
    })
    .join("");

  const grid = [0, 0.25, 0.5, 0.75, 1]
    .map((ratio) => {
      const y = top + chartHeight - ratio * chartHeight;
      const label = formatNumber(maxRain * ratio, 1);
      return `
        <line x1="${left}" x2="${width - right}" y1="${round(y)}" y2="${round(y)}" stroke="${gridColor}" stroke-width="1"></line>
        <text x="0" y="${round(y + 4)}" fill="${textColor}" font-size="11">${escapeHtml(label)}</text>
      `;
    })
    .join("");

  const labels = buildTimeLabels(points, hass)
    .map(
      ({ x, label, anchor }) =>
        `<text x="${round(x)}" y="${height - 8}" text-anchor="${anchor}" fill="${textColor}" font-size="11">${escapeHtml(label)}</text>`
    )
    .join("");

  return `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Bandabou rain forecast">
      ${grid}
      ${bars}
      <path d="${line}" fill="none" stroke="${chanceColor}" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
      ${dots}
      ${labels}
    </svg>
  `;
}

function buildTimeLabels(points, hass) {
  const locale = hass?.locale?.language;
  const labels = [
    { index: 0, anchor: "start" },
    { index: Math.floor((points.length - 1) / 2), anchor: "middle" },
    { index: points.length - 1, anchor: "end" },
  ];

  const seen = new Set();
  return labels
    .filter(({ index }) => {
      if (seen.has(index)) {
        return false;
      }
      seen.add(index);
      return true;
    })
    .map(({ index, anchor }) => ({
      x:
        points.length === 1
          ? 38 + (640 - 38 - 18) / 2
          : 38 + (index / (points.length - 1)) * (640 - 38 - 18),
      anchor,
      label: new Intl.DateTimeFormat(locale, {
        hour: "2-digit",
        minute: "2-digit",
      }).format(new Date(points[index].timestamp)),
    }));
}

function formatEntityState(hass, entityId, fallbackUnit) {
  const stateObj = hass.states[entityId];
  if (!stateObj || stateObj.state === "unknown" || stateObj.state === "unavailable") {
    return "-";
  }

  const value = Number(stateObj.state);
  const unit = stateObj.attributes.unit_of_measurement || fallbackUnit || "";
  if (Number.isFinite(value)) {
    return `${formatNumber(value, unit === "%" || unit === "d" ? 0 : 1)} ${unit}`.trim();
  }
  return `${stateObj.state} ${unit}`.trim();
}

function formatNumber(value, decimals) {
  if (!Number.isFinite(value)) {
    return "0";
  }

  return value.toLocaleString(undefined, {
    maximumFractionDigits: decimals,
    minimumFractionDigits: decimals > 0 && value > 0 && value < 1 ? decimals : 0,
  });
}

function round(value) {
  return Math.round(value * 100) / 100;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

customElements.define("bandabou-rain-card", BandabouRainCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "bandabou-rain-card",
  name: "Bandabou Rain Card",
  description: "Rain forecast graph for the Bandabou Rain integration",
});
