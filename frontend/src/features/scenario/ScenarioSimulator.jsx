import React, { useState } from "react";
import { SlidersHorizontal } from "lucide-react";

import { Button } from "../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { fetchScenario } from "../../services/api";

export function ScenarioSimulator({ ticker, horizon, onScenario }) {
  const [form, setForm] = useState({ next_open_pct: 0.5, vix: 0.1, volume_spike: 0.2 });
  const [loading, setLoading] = useState(false);

  const updateField = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: Number(value) }));
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const response = await fetchScenario({ ticker, horizon, adjustments: form });
      onScenario?.(response.prediction);
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error("Scenario request failed", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <SlidersHorizontal className="h-5 w-5" /> Scenario Simulator
        </CardTitle>
        <CardDescription>Adjust inputs to explore what-if forecasts. Updated locally and via RL engine snapshot.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <div className="grid gap-3">
          <label className="flex flex-col gap-1">
            <span className="text-muted-foreground">Next Open %</span>
            <input
              type="range"
              min={-2}
              max={2}
              step={0.1}
              value={form.next_open_pct}
              onChange={(event) => updateField("next_open_pct", event.target.value)}
            />
            <span className="font-mono">{form.next_open_pct}%</span>
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-muted-foreground">VIX</span>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={form.vix}
              onChange={(event) => updateField("vix", event.target.value)}
            />
            <span className="font-mono">{form.vix}</span>
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-muted-foreground">Volume Spike</span>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={form.volume_spike}
              onChange={(event) => updateField("volume_spike", event.target.value)}
            />
            <span className="font-mono">{form.volume_spike}</span>
          </label>
        </div>
        <Button onClick={handleSubmit} disabled={loading} className="w-full">
          {loading ? "Simulating…" : "Run Simulation"}
        </Button>
      </CardContent>
    </Card>
  );
}
