import { useEffect, useMemo, useRef } from 'react';
import {
  createChart,
  ColorType,
  LineStyle,
  type IChartApi,
  type ISeriesApi,
  type LineData,
  type UTCTimestamp,
} from 'lightweight-charts';
import type { Tick } from '../types';
import { isoToUnix } from '../lib/utils';

/**
 * Build a strictly-ascending, time-unique LineData[] from raw points.
 * lightweight-charts throws on duplicate or out-of-order times, so we keep
 * the last value per timestamp and sort.
 */
function buildSeries(points: { time: number; value: number }[]): LineData[] {
  const byTime = new Map<number, number>();
  for (const p of points) {
    if (!Number.isFinite(p.time) || !Number.isFinite(p.value)) continue;
    byTime.set(p.time, p.value);
  }
  return Array.from(byTime.entries())
    .sort((a, b) => a[0] - b[0])
    .map(([time, value]) => ({ time: time as UTCTimestamp, value }));
}

export function PriceChart({ ticks }: { ticks: Tick[] }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const actualRef = useRef<ISeriesApi<'Line'> | null>(null);
  const predictedRef = useRef<ISeriesApi<'Line'> | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#94a3b8',
        fontFamily: 'ui-monospace, monospace',
      },
      grid: {
        vertLines: { color: 'rgba(31,41,55,0.4)' },
        horzLines: { color: 'rgba(31,41,55,0.4)' },
      },
      rightPriceScale: { borderColor: '#1f2937' },
      timeScale: {
        borderColor: '#1f2937',
        timeVisible: true,
        secondsVisible: true,
      },
      crosshair: { mode: 0 },
    });

    const actual = chart.addLineSeries({
      color: '#38bdf8',
      lineWidth: 2,
      title: 'Actual',
      priceLineVisible: false,
      lastValueVisible: true,
    });

    const predicted = chart.addLineSeries({
      color: '#f59e0b',
      lineWidth: 2,
      lineStyle: LineStyle.Dashed,
      title: 'Predicted (t+10s)',
      priceLineVisible: false,
      lastValueVisible: true,
    });

    chartRef.current = chart;
    actualRef.current = actual;
    predictedRef.current = predicted;

    return () => {
      chart.remove();
      chartRef.current = null;
      actualRef.current = null;
      predictedRef.current = null;
    };
  }, []);

  const { actualData, predictedData } = useMemo(() => {
    const actualPts = ticks.map((t) => ({ time: isoToUnix(t.timestamp), value: t.price }));
    const predictedPts = ticks.map((t) => ({
      time: isoToUnix(t.target_at),
      value: t.predicted_price,
    }));
    return {
      actualData: buildSeries(actualPts),
      predictedData: buildSeries(predictedPts),
    };
  }, [ticks]);

  useEffect(() => {
    actualRef.current?.setData(actualData);
    predictedRef.current?.setData(predictedData);
  }, [actualData, predictedData]);

  return (
    <div className="relative h-full w-full">
      <div ref={containerRef} className="h-full w-full" />
      {ticks.length === 0 && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center text-sm text-muted">
          Waiting for live ticks…
        </div>
      )}
    </div>
  );
}
