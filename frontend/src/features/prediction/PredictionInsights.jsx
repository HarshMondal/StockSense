import React from "react";
import { BrainCircuit, CheckCircle2 } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";

const defaultReasons = [
  { label: "Momentum", description: "Price momentum +1.8σ above mean" },
  { label: "Volume", description: "Volume spike detected over 15m" },
  { label: "RSI", description: "RSI trending toward overbought" },
];

const defaultStats = [
  { label: "Hit Rate (30d)", value: "76%" },
  { label: "Average Return", value: "+1.2%" },
  { label: "Confidence", value: "High" },
];

export function PredictionInsights({ prediction, horizon, onHorizonChange, horizons }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-xl">
              <BrainCircuit className="h-5 w-5" /> Prediction Intelligence
            </CardTitle>
            <CardDescription>Understand the factors influencing the current forecast.</CardDescription>
          </div>
          <Badge variant="outline">Confidence {Math.round((prediction?.confidence ?? 0.5) * 100)}%</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <Tabs value={horizon} onValueChange={onHorizonChange}>
          <TabsList>
            {horizons.map((item) => (
              <TabsTrigger key={item} value={item}>
                {item}
              </TabsTrigger>
            ))}
          </TabsList>
          <TabsContent value={horizon} className="space-y-3">
            <div className="grid gap-3 sm:grid-cols-2">
              {defaultReasons.map((reason) => (
                <div key={reason.label} className="rounded-lg border bg-card/60 p-3 text-sm">
                  <div className="font-semibold">{reason.label}</div>
                  <div className="text-muted-foreground">{reason.description}</div>
                </div>
              ))}
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              {defaultStats.map((stat) => (
                <div key={stat.label} className="rounded-lg bg-muted/50 p-3 text-sm">
                  <div className="text-muted-foreground">{stat.label}</div>
                  <div className="text-lg font-semibold">{stat.value}</div>
                </div>
              ))}
            </div>
          </TabsContent>
        </Tabs>
        <div className="flex items-center gap-2 rounded-lg border border-dashed p-3 text-xs text-muted-foreground">
          <CheckCircle2 className="h-4 w-4" />
          The online learner continuously adapts with every incoming tick. Latest checkpoint saved at {prediction?.updated_at ?? "--"}.
        </div>
      </CardContent>
    </Card>
  );
}
