const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function fetchJson(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}`);
  }
  return response.json();
}

export async function fetchPredictionSnapshot(ticker, horizon, features) {
  const body = features ? JSON.stringify({ features }) : undefined;
  return fetchJson(`/api/predictions/${ticker}/${horizon}/snapshot/`, {
    method: body ? "POST" : "GET",
    body,
  });
}

export async function runBacktest(input) {
  return fetchJson("/api/backtest/", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function fetchBaselines(input) {
  return fetchJson("/api/baselines/", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function fetchScenario(input) {
  return fetchJson("/api/what-if/", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function fetchModelCard() {
  return fetchJson("/api/meta/model-card/");
}

export async function fetchProvenance() {
  return fetchJson("/api/meta/provenance/");
}

export async function fetchVersion() {
  return fetchJson("/api/meta/version/");
}
