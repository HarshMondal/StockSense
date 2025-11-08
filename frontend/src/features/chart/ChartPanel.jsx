import React from "react";
import { LineChart, TrendingUp } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "../../components/ui/tooltip";

export function ChartPanel({ ticker, horizon, prediction, latency, onScreenshot }) {
  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-center justify-between gap-4">
        <div>
          <CardTitle className="flex items-center gap-2 text-2xl">
            <LineChart className="h-5 w-5" /> {ticker}
          </CardTitle>
          <CardDescription>
            {horizon.toUpperCase()} horizon • Live prediction updated {prediction?.updated_at ? new Date(prediction.updated_at).toLocaleTimeString() : "--"}
          </CardDescription>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="success">Latency: {latency ?? "--"} ms</Badge>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger className="rounded-md border px-2 py-1 text-xs">
                Export
              </TooltipTrigger>
              <TooltipContent>
                <p>Downloads the current chart screenshot.</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex h-72 items-center justify-center rounded-lg border border-dashed">
          <div className="text-center text-sm text-muted-foreground">
            <TrendingUp className="mx-auto mb-2 h-6 w-6" />
            Real-time chart renders here. Integrate lightweight-charts or preferred canvas library to display OHLCV, indicators,
            and prediction overlays.
          </div>
        </div>
        {prediction ? (
          <div className="rounded-lg border bg-muted/50 p-4 text-sm">
            <div className="font-semibold">Prediction preview</div>
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs sm:grid-cols-3">
              {(prediction.points ?? []).map(([timestamp, price], index) => (
                <div key={timestamp} className="flex flex-col rounded-md bg-background/60 p-2 shadow-sm">
                  <span className="text-muted-foreground">T+{index + 1}</span>
                  <span className="font-semibold">{price.toFixed(2)}</span>
                </div>
              ))}
            </div>
            <div className="mt-2 text-muted-foreground">
              Confidence {Math.round(prediction.confidence * 100)}% • Updated {new Date(prediction.updated_at).toLocaleTimeString()}
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
