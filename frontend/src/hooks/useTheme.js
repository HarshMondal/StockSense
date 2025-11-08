import { useEffect, useState } from "react";

const STORAGE_KEY = "stocksense-theme";

function readStorage() {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch (error) {
    return null;
  }
}

function writeStorage(value) {
  if (typeof window === "undefined") {
    return;
  }
  try {
    localStorage.setItem(STORAGE_KEY, value);
  } catch (error) {
    // ignore storage errors (e.g., strict privacy mode)
  }
}

export function useTheme() {
  const [theme, setTheme] = useState(() => readStorage() || "light");

  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove("light", "dark");
    root.classList.add(theme);
    writeStorage(theme);
  }, [theme]);

  return { theme, setTheme };
}
