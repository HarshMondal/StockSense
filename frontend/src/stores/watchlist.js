const STORAGE_KEY = "stocksense-watchlist";

function readWatchlist() {
  if (typeof window === "undefined") {
    return ["AAPL", "MSFT", "GOOG"];
  }
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : ["AAPL", "MSFT", "GOOG"];
  } catch (error) {
    return ["AAPL", "MSFT", "GOOG"];
  }
}

function writeWatchlist(list) {
  if (typeof window === "undefined") {
    return;
  }
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
  } catch (error) {
    // ignore when persistence disabled
  }
}

export function loadWatchlist() {
  return readWatchlist();
}

export function saveWatchlist(list) {
  writeWatchlist(list);
}
