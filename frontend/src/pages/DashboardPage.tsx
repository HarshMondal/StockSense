import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import * as Tabs from '@radix-ui/react-tabs';
import { AppHeader } from '../components/AppHeader';
import { PriceChart } from '../components/PriceChart';
import { EvaluationPanel } from '../components/EvaluationPanel';
import { useStockSocket } from '../hooks/useStockSocket';
import { useAuth } from '../context/AuthContext';
import { HORIZONS, type Horizon } from '../types';
import { cn, fmtPrice } from '../lib/utils';

const SOCKET_LABEL: Record<string, { text: string; cls: string }> = {
  connecting: { text: 'connecting…', cls: 'text-warn' },
  open: { text: 'connected', cls: 'text-good' },
  closed: { text: 'reconnecting…', cls: 'text-warn' },
  unauthorized: { text: 'unauthorized', cls: 'text-bad' },
  'bad-horizon': { text: 'invalid horizon', cls: 'text-bad' },
};

export function DashboardPage() {
  const params = useParams();
  const navigate = useNavigate();
  const { refresh } = useAuth();
  const ticker = (params.ticker ?? '').toUpperCase();
  const [horizon, setHorizon] = useState<Horizon>('intraday');

  const { latest, ticks, status } = useStockSocket(ticker, horizon);

  // If the session expires mid-session the WS closes with 4401; bounce to login.
  useEffect(() => {
    if (status === 'unauthorized') {
      void refresh();
      navigate('/login', { replace: true });
    }
  }, [status, refresh, navigate]);

  const price = latest?.price ?? null;
  const source = latest?.source ?? null;
  const socketLabel = SOCKET_LABEL[status] ?? SOCKET_LABEL.connecting;

  const predReturn = latest?.predicted_return ?? null;

  return (
    <div className="min-h-screen bg-bg">
      <AppHeader ticker={ticker} price={price} source={source} />

      <main className="mx-auto max-w-7xl px-4 py-5">
        {/* Controls row */}
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <Tabs.Root value={horizon} onValueChange={(v) => setHorizon(v as Horizon)}>
            <Tabs.List className="inline-flex rounded-lg border border-line bg-bg-card p-1">
              {HORIZONS.map((h) => (
                <Tabs.Trigger
                  key={h}
                  value={h}
                  className={cn(
                    'rounded-md px-3 py-1.5 text-sm font-medium capitalize transition-colors',
                    'text-muted data-[state=active]:bg-accent data-[state=active]:text-slate-950',
                  )}
                >
                  {h}
                </Tabs.Trigger>
              ))}
            </Tabs.List>
          </Tabs.Root>

          <div className="flex items-center gap-2 text-xs">
            <span
              className={cn(
                'inline-block h-2 w-2 rounded-full',
                status === 'open'
                  ? 'bg-good'
                  : status === 'unauthorized' || status === 'bad-horizon'
                    ? 'bg-bad'
                    : 'bg-warn',
              )}
            />
            <span className={socketLabel.cls}>{socketLabel.text}</span>
          </div>
        </div>

        {/* Main grid: chart (wide) + evaluation panel (hero) */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <div className="card flex flex-col p-4">
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <Legend color="#38bdf8" label="Actual" />
                  <Legend color="#f59e0b" label="Predicted (t+10s)" dashed />
                </div>
                {predReturn != null && (
                  <span className="font-mono text-xs text-muted">
                    pred return {(predReturn * 100).toFixed(4)}%
                  </span>
                )}
              </div>
              <div className="h-[420px]">
                <PriceChart ticks={ticks} />
              </div>

              {latest?.last_prediction && (
                <div className="mt-3 grid grid-cols-2 gap-2 border-t border-line pt-3 text-xs sm:grid-cols-4">
                  <Stat
                    label="Last predicted"
                    value={`$${fmtPrice(latest.last_prediction.predicted_price)}`}
                  />
                  <Stat
                    label="Last actual"
                    value={`$${fmtPrice(latest.last_prediction.actual_price)}`}
                  />
                  <Stat
                    label="Abs error"
                    value={fmtPrice(latest.last_prediction.abs_error, 4)}
                  />
                  <Stat
                    label="Beat naive?"
                    value={latest.last_prediction.hit ? 'yes' : 'no'}
                    good={latest.last_prediction.hit}
                  />
                </div>
              )}
            </div>
          </div>

          <div className="lg:col-span-1">
            <EvaluationPanel
              ticker={ticker}
              horizon={horizon}
              rollingMaeLive={latest?.rolling_mae ?? null}
            />
          </div>
        </div>
      </main>
    </div>
  );
}

function Legend({ color, label, dashed }: { color: string; label: string; dashed?: boolean }) {
  return (
    <div className="flex items-center gap-2 text-xs text-muted">
      <span
        className="inline-block h-0 w-5 border-t-2"
        style={{ borderColor: color, borderStyle: dashed ? 'dashed' : 'solid' }}
      />
      {label}
    </div>
  );
}

function Stat({ label, value, good }: { label: string; value: string; good?: boolean }) {
  return (
    <div>
      <div className="text-muted">{label}</div>
      <div className={cn('font-mono tabular-nums', good ? 'text-good' : 'text-slate-100')}>
        {value}
      </div>
    </div>
  );
}
