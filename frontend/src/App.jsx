import React, { useCallback, useMemo, useState } from "react";
import { Github, Moon, SunMedium } from "lucide-react";

import { DashboardLayout } from "./components/layout/DashboardLayout";
import { Button } from "./components/ui/button";
import { Switch } from "./components/ui/switch";
import { ChartPanel } from "./features/chart/ChartPanel";
import { PredictionInsights } from "./features/prediction/PredictionInsights";
import { ScenarioSimulator } from "./features/scenario/ScenarioSimulator";
import { WatchlistPanel } from "./features/watchlist/WatchlistPanel";
import { BacktestPanel } from "./features/backtest/BacktestPanel";
import { useTheme } from "./hooks/useTheme";
import { useWebSocket } from "./hooks/useWebSocket";

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL;
const DEFAULT_TICKER = "AAPL";
const HORIZONS = ["intraday", "daily", "weekly"];

export default function App() {
  const { theme, setTheme } = useTheme();
  const [ticker, setTicker] = useState(DEFAULT_TICKER);
  const [horizon, setHorizon] = useState(HORIZONS[0]);
  const [prediction, setPrediction] = useState(null);
  const [latency, setLatency] = useState(null);

  const predictionSocketUrl = useMemo(() => `${WS_BASE_URL}/ws/predictions/${ticker}/${horizon}/`, [ticker, horizon]);

  const handleSocketMessage = useCallback(
    (message) => {
      if (message.type === "prediction") {
        setPrediction(message.payload);
      } else if (message.type === "pong") {
        setLatency(Date.now() - new Date(message.timestamp).getTime());
      }
    },
    [setLatency, setPrediction]
  );

  useWebSocket(predictionSocketUrl, {
    onMessage: handleSocketMessage,
  });

  const toggleTheme = useCallback(
    (isDark) => {
      setTheme(isDark ? "dark" : "light");
    },
    [setTheme]
  );

  const handleScenario = useCallback((value) => {
    setPrediction(value);
  }, [setPrediction]);

  return (
    <DashboardLayout
      header={<Header theme={theme} onToggleTheme={toggleTheme} ticker={ticker} horizon={horizon} />}
      sidebar={<Sidebar ticker={ticker} setTicker={setTicker} />}
      footer={<Footer />}
    >
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          <ChartPanel ticker={ticker} horizon={horizon} prediction={prediction} latency={latency} onScreenshot={() => {}} />
          <PredictionInsights
            prediction={prediction}
            horizon={horizon}
            horizons={HORIZONS}
            onHorizonChange={(value) => setHorizon(value)}
          />
        </div>
        <div className="space-y-4">
          <ScenarioSimulator ticker={ticker} horizon={horizon} onScenario={handleScenario} />
          <BacktestPanel ticker={ticker} horizon={horizon} />
        </div>
      </div>
    </DashboardLayout>
  );
}

function Header({ theme, onToggleTheme, ticker, horizon }) {
  return (
    <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-3">
      <div>
        <div className="flex items-center gap-2 text-xl font-semibold">
          <span className="rounded-md bg-primary px-2 py-1 text-primary-foreground">Stocksense</span>
          <span className="text-sm text-muted-foreground">AI Market Terminal</span>
        </div>
        <div className="text-xs text-muted-foreground">Streaming forecasts for {ticker} on the {horizon} horizon.</div>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <SunMedium className="h-4 w-4" />
          <Switch checked={theme === "dark"} onCheckedChange={(checked) => onToggleTheme(checked)} />
          <Moon className="h-4 w-4" />
        </div>
        <Button variant="outline" size="sm" asChild>
          <a href="https://github.com" target="_blank" rel="noreferrer">
            <Github className="mr-2 h-4 w-4" /> GitHub
          </a>
        </Button>
      </div>
    </div>
  );
}

function Sidebar({ ticker, setTicker }) {
  return (
    <div className="space-y-4">
      <WatchlistPanel onSelect={setTicker} activeTicker={ticker} />
      <div className="rounded-lg border bg-muted/30 p-4 text-xs text-muted-foreground">
        Market data provided by Finnhub free tier. Ensure API key is configured in <code>frontend/.env</code> and backend `.env`.
      </div>
    </div>
  );
}

function Footer() {
  const appName = import.meta.env.VITE_APP_NAME ?? "Stocksense";
  return <div>Build {appName} • Online RL prototype • {new Date().getFullYear()}</div>;
}
