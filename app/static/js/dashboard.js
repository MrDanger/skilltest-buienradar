const logNode = document.getElementById("activity-log");
const toastContainer = document.getElementById("toast-container");
const MAX_LOG_LINES = 80;
let chart;
let lastSeriesSignature = null;

function log(message) {
  const stamp = new Date().toLocaleTimeString();
  const next = [`[${stamp}] ${message}`, ...logNode.textContent.split("\n")].slice(0, MAX_LOG_LINES);
  logNode.textContent = next.join("\n");
}

function notify(message, level = "info", ttlMs = 3500) {
  const toast = document.createElement("div");
  toast.className = `toast ${level}`;
  toast.textContent = message;
  toastContainer.appendChild(toast);
  window.setTimeout(() => {
    toast.remove();
  }, ttlMs);
}

async function withButtonLoading(buttonId, runningText, fn) {
  const btn = document.getElementById(buttonId);
  const original = btn.textContent;
  btn.disabled = true;
  btn.textContent = runningText;
  try {
    return await fn();
  } finally {
    btn.disabled = false;
    btn.textContent = original;
  }
}

async function callApi(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || `Request failed (${response.status})`);
  }
  return response.json();
}

function setText(id, value) {
  document.getElementById(id).textContent = value;
}

function renderPointsTable(seriesData) {
  const tbody = document.getElementById("temp-points-body");
  if (!seriesData.length) {
    tbody.innerHTML = `<tr><td colspan="2">No data yet.</td></tr>`;
    return;
  }

  const rows = [...seriesData].reverse();
  tbody.innerHTML = rows
    .map(
      (point) =>
        `<tr><td>${point.timestamp}</td><td>${Number(point.avg_temperature).toFixed(2)}</td></tr>`
    )
    .join("");
}

function renderScheduler(status) {
  const text = status.active
    ? `Status: Running every ${status.interval_minutes} minute(s)`
    : "Status: Stopped";
  setText("scheduler-status", text);
  setText("scheduler-next", `Next run: ${status.next_run_time || "-"}`);
  if (status.interval_minutes !== null && status.interval_minutes !== undefined) {
    document.getElementById("interval").value = String(status.interval_minutes);
  }
}

async function refreshAnalysis() {
  const summary = await callApi("/api/dashboard/summary?limit=72");
  const highest = summary.highest_temperature;
  const avg = summary.average_temperature;
  const gap = summary.biggest_feel_gap;
  const north = summary.north_sea_station;
  const seriesData = summary.temperature_series || [];

  setText("highest-temp", `${highest.temperature.toFixed(1)} C`);
  setText("highest-meta", `${highest.stationname} @ ${highest.timestamp}`);
  setText(
    "avg-temp",
    avg.average_temperature === null ? "No data" : `${avg.average_temperature.toFixed(2)} C`
  );
  setText("feel-gap", `${gap.temperature_gap.toFixed(1)} C`);
  setText("feel-meta", `${gap.stationname} @ ${gap.timestamp}`);
  setText("north-sea", north.stationname);
  setText("north-sea-meta", `${north.regio || "-"} (${north.lat || "-"}, ${north.lon || "-"})`);

  const labels = seriesData.map((x) => x.timestamp);
  const values = seriesData.map((x) => x.avg_temperature);
  setText("points-count", `${values.length} points`);
  renderPointsTable(seriesData);
  const currentSignature = JSON.stringify({
    count: seriesData.length,
    latest: seriesData.length ? seriesData[seriesData.length - 1].timestamp : null,
  });
  const changed = lastSeriesSignature !== currentSignature;
  lastSeriesSignature = currentSignature;

  if (!chart) {
    const ctx = document.getElementById("tempChart");
    chart = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "Avg Temperature",
            data: values,
            tension: 0.25,
            borderColor: "#22d3ee",
            backgroundColor: "rgba(34, 211, 238, 0.25)",
            fill: true,
            pointRadius: 3,
            pointHoverRadius: 5,
            pointBackgroundColor: "#ef4444",
            pointBorderColor: "#ffffff",
            pointBorderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        normalized: true,
        scales: {
          y: {
            ticks: { color: "#cbd5e1" },
            grid: { color: "rgba(203, 213, 225, 0.16)" },
          },
          x: {
            ticks: { color: "#94a3b8", maxTicksLimit: 6 },
            grid: { display: false },
          },
        },
        plugins: {
          legend: {
            labels: { color: "#e2e8f0" },
          },
          decimation: {
            enabled: true,
            algorithm: "lttb",
            samples: 60,
          },
        },
      },
    });
  } else {
    chart.data.labels = labels;
    chart.data.datasets[0].data = values;
    chart.update("none");
  }
  return changed;
}

async function refreshScheduler() {
  const status = await callApi("/api/scheduler/status");
  renderScheduler(status);
}

document.getElementById("btn-ingest").addEventListener("click", async () => {
  await withButtonLoading("btn-ingest", "Ingesting...", async () => {
    try {
      const result = await callApi("/api/ingestion/once", { method: "POST" });
      log(
        `Ingestion complete. stations_upserted=${result.stations_upserted}, measurements_inserted=${result.measurements_inserted}`
      );

      const changed = await refreshAnalysis();
      await refreshScheduler();

      if (result.measurements_inserted === 0) {
        notify("No new measurements were inserted (already up to date).", "warning");
      } else {
        notify(`Ingested ${result.measurements_inserted} new measurements.`, "success");
      }
      if (!changed) {
        notify("Chart data unchanged after ingestion.", "info");
      }
    } catch (error) {
      log(`Ingestion failed: ${error.message}`);
      notify(`Ingestion failed: ${error.message}`, "error", 5000);
    }
  });
});

document.getElementById("btn-refresh").addEventListener("click", async () => {
  await withButtonLoading("btn-refresh", "Refreshing...", async () => {
    try {
      const changed = await refreshAnalysis();
      await refreshScheduler();
      log("Dashboard refreshed.");
      notify(changed ? "Insights refreshed with latest data." : "No new data since last refresh.", changed ? "success" : "warning");
    } catch (error) {
      log(`Refresh failed: ${error.message}`);
      notify(`Refresh failed: ${error.message}`, "error", 5000);
    }
  });
});

document.getElementById("btn-start").addEventListener("click", async () => {
  const interval = Number(document.getElementById("interval").value);
  try {
    const result = await callApi(`/api/scheduler/start?minutes=${interval}`, { method: "POST" });
    renderScheduler(result);
    log(`Scheduler started with ${interval} minute interval.`);
    notify(`Scheduler started: every ${interval} minute(s).`, "success");
  } catch (error) {
    log(`Start scheduler failed: ${error.message}`);
    notify(`Start scheduler failed: ${error.message}`, "error", 5000);
  }
});

document.getElementById("btn-stop").addEventListener("click", async () => {
  try {
    const result = await callApi("/api/scheduler/stop", { method: "POST" });
    renderScheduler(result);
    log("Scheduler stopped.");
    notify("Scheduler stopped.", "warning");
  } catch (error) {
    log(`Stop scheduler failed: ${error.message}`);
    notify(`Stop scheduler failed: ${error.message}`, "error", 5000);
  }
});

(async function bootstrap() {
  await refreshScheduler().catch((error) => {
    log(`Scheduler status load failed: ${error.message}`);
  });

  await refreshAnalysis()
    .then(() => log("Dashboard ready."))
    .catch((error) => {
      log(`Initial analysis load failed: ${error.message}. Run ingestion first.`);
      notify("No analysis data yet. Click 'Ingest Latest Snapshot'.", "warning");
    });
})();
