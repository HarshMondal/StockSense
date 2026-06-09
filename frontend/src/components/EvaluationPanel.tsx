import useSWR from 'swr';
import { CheckCircle2, MinusCircle, Activity } from 'lucide-react';
import { api } from '../lib/api';
import type { AccuracyResponse, Horizon } from '../types';
import { cn, fmtAccuracy, fmtPrice } from '../lib/utils';
import { Sparkline } from './Sparkline';

interface EvaluationPanelProps {
  ticker: string;
  horizon: Horizon;
  rollingMaeLive?: number | null;
}

function MaeRow({
  label,
  value,
  highlight,
}: {
  label: string;
  value: number | null;
  highlight?: 'good' | 'neutral';
}) {
  return (
    <div className="flex items-center justify-between py-1.5 text-sm">
      <span className="text-muted">{label}</span>
      <span
        className={cn(
          'font-mono tabular-nums',
          highlight === 'good' ? 'text-good' : 'text-slate-100',
        )}
      >
        {fmtPrice(value, 4)}
      </span>
    </div>
  );
}

export function EvaluationPanel({ ticker, horizon, rollingMaeLive }: EvaluationPanelProps) {
  const { data, error, isLoading } = useSWR<AccuracyResponse>(
    ['accuracy', ticker, horizon],
    () => api.accuracy(ticker, horizon),
    { refreshInterval: 5000, revalidateOnFocus: false, keepPreviousData: true },
  );

  const beats = data?.beats_naive ?? false;
  const rollingMae = rollingMaeLive ?? data?.model.rolling_mae ?? null;
  const trend = data?.mae_trend?.map((p) => p.abs_error) ?? [];

  return (
    <section className="card flex flex-col gap-4 p-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-accent" />
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-200">
            Evaluation
          </h2>
        </div>
        <span className="rounded-md bg-bg-soft px-2 py-0.5 text-xs text-muted">
          {data ? `${data.count} resolved` : '—'}
        </span>
      </div>

      {/* Hero: beats baseline badge */}
      <div
        className={cn(
          'flex items-center gap-3 rounded-xl border px-4 py-4',
          beats
            ? 'border-good/40 bg-good/10'
            : 'border-line bg-bg-soft',
        )}
      >
        {beats ? (
          <CheckCircle2 className="h-9 w-9 shrink-0 text-good" />
        ) : (
          <MinusCircle className="h-9 w-9 shrink-0 text-muted" />
        )}
        <div>
          <div className={cn('text-lg font-bold', beats ? 'text-good' : 'text-slate-200')}>
            {beats ? 'Beats naive baseline' : 'Not beating naive (yet)'}
          </div>
          <div className="text-xs text-muted">
            Model MAE vs naive MAE over {data?.count ?? 0} resolved predictions
          </div>
        </div>
      </div>

      {/* Top stats */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-lg border border-line bg-bg-soft p-3">
          <div className="text-xs text-muted">Directional accuracy</div>
          <div className="mt-1 text-2xl font-bold tabular-nums text-accent">
            {fmtAccuracy(data?.model.directional_accuracy)}
          </div>
          <div className="mt-0.5 text-[11px] text-muted">
            naive {fmtAccuracy(data?.naive.directional_accuracy)}
          </div>
        </div>
        <div className="rounded-lg border border-line bg-bg-soft p-3">
          <div className="text-xs text-muted">Model updates</div>
          <div className="mt-1 text-2xl font-bold tabular-nums text-slate-100">
            {data?.model.update_count ?? '—'}
          </div>
          <div className="mt-0.5 text-[11px] text-muted">
            times the model has learned
          </div>
        </div>
      </div>

      {/* MAE comparison */}
      <div className="rounded-lg border border-line bg-bg-soft p-3">
        <div className="mb-1 text-xs font-medium uppercase tracking-wide text-muted">
          Mean absolute error (lower is better)
        </div>
        <MaeRow
          label="Model"
          value={data?.model.mae ?? null}
          highlight={beats ? 'good' : 'neutral'}
        />
        <MaeRow label="Naive" value={data?.naive.mae ?? null} />
        <MaeRow label="Random walk" value={data?.random_walk.mae ?? null} />
        <div className="mt-2 flex items-center justify-between border-t border-line pt-2 text-sm">
          <span className="text-muted">Rolling MAE</span>
          <span className="font-mono tabular-nums text-slate-100">
            {fmtPrice(rollingMae, 4)}
          </span>
        </div>
      </div>

      {/* Trend sparkline */}
      <div className="rounded-lg border border-line bg-bg-soft p-3">
        <div className="mb-2 flex items-center justify-between">
          <span className="text-xs font-medium uppercase tracking-wide text-muted">
            Abs-error trend
          </span>
          {error && <span className="text-[11px] text-bad">offline</span>}
          {isLoading && !data && <span className="text-[11px] text-muted">loading…</span>}
        </div>
        <Sparkline values={trend} stroke="#38bdf8" width={260} height={48} />
      </div>

      <p className="text-[11px] leading-relaxed text-muted">
        At a 10-second horizon, price is near-random-walk. We measure ourselves against naive
        baselines — and show when we don&apos;t beat them.
      </p>
    </section>
  );
}
