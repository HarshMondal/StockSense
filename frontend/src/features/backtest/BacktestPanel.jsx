import React, { useState } from "react";
import { BarChart3 } from "lucide-react";

import { Button } from "../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { fetchBaselines, runBacktest } from "../../services/api";

export function BacktestPanel({ ticker, horizon }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [baselines, setBaselines] = useState([]);

  const execute = async () => {
    setLoading(true);
    try {
      const [backtest, baselineData] = await Promise.all([
        runBacktest({ ticker, horizon }),
        fetchBaselines({ ticker, horizon }),
      ]);
      setResult(backtest.result);
      setBaselines(baselineData.baselines);
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error("Backtest failed", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <BarChart3 className="h-5 w-5" /> Backtesting & Benchmarks
        </CardTitle>
        <CardDescription>Replay forecasts over historical windows and compare against baselines.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <Button onClick={execute} disabled={loading} className="w-full">
          {loading ? "Running backtest…" : "Run backtest"}
        </Button>
        {result ? (
          <div className="space-y-3 rounded-lg border bg-muted/40 p-4">
            <div className="grid gap-2 sm:grid-cols-3">
              <Stat label="CAGR" value={`${Math.round(result.cagr * 100)}%`} />
              <Stat label="Sharpe" value={result.sharpe.toFixed(2)} />
              <Stat label="Max Drawdown" value={`${Math.round(result.max_drawdown * 100)}%`} />
            </div>
            <div>
              <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Baseline comparison
              </div>
              <ul className="space-y-2">
                {baselines.map((item) => (
                  <li key={item.name} className="flex items-center justify-between rounded-md bg-background/80 p-3">
                    <span className="capitalize">{item.name.replace("_", " ")}</span>
                    <span className="font-mono text-xs">
                      CAGR {Math.round(item.cagr * 100)}% • Sharpe {item.sharpe.toFixed(2)}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ) : (
          <p className="text-xs text-muted-foreground">
            Configure start/end windows and custom presets in future iterations. Current implementation returns summary metrics
            using backend placeholders.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function Stat({ label, value }) {
  return (
    <div className="rounded-md border border-dashed bg-background/80 p-3">
      <div className="text-muted-foreground">{label}</div>
      <div className="text-lg font-semibold">{value}</div>
    </div>
  );
}
