import React, { useEffect, useState } from "react";
import { ListChecks, PlusCircle } from "lucide-react";

import { Button } from "../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { loadWatchlist, saveWatchlist } from "../../stores/watchlist";

export function WatchlistPanel({ onSelect, activeTicker }) {
  const [items, setItems] = useState(() => loadWatchlist());
  const [input, setInput] = useState("");

  useEffect(() => {
    saveWatchlist(items);
  }, [items]);

  const addTicker = () => {
    if (!input) return;
    const symbol = input.toUpperCase();
    if (!items.includes(symbol)) {
      setItems([...items, symbol]);
    }
    setInput("");
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <ListChecks className="h-5 w-5" /> Watchlist
        </CardTitle>
        <CardDescription>Client-side watchlist stored locally. Strict privacy mode clears data.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <div className="flex gap-2">
          <input
            className="flex-1 rounded-md border border-input bg-background px-3 py-2"
            placeholder="Add ticker"
            value={input}
            onChange={(event) => setInput(event.target.value.toUpperCase())}
          />
          <Button variant="secondary" onClick={addTicker}>
            <PlusCircle className="mr-2 h-4 w-4" /> Add
          </Button>
        </div>
        <ul className="space-y-2">
          {items.map((symbol) => (
            <li key={symbol}>
              <button
                type="button"
                onClick={() => onSelect(symbol)}
                className={`flex w-full items-center justify-between rounded-md border px-3 py-2 text-left ${
                  activeTicker === symbol ? "border-primary bg-primary/10" : "border-border"
                }`}
              >
                <span>{symbol}</span>
                {activeTicker === symbol ? <span className="text-xs text-primary">Active</span> : null}
              </button>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
