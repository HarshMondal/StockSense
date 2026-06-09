import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, TrendingUp } from 'lucide-react';
import { api } from '../lib/api';
import type { SearchResult } from '../types';
import { AppHeader } from '../components/AppHeader';

export function SearchPage() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const q = query.trim();
    if (q.length < 1) {
      setResults([]);
      setError(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    const handle = setTimeout(async () => {
      try {
        const res = await api.search(q);
        if (!cancelled) {
          setResults(res.results);
          setError(null);
        }
      } catch {
        if (!cancelled) setError('Search failed.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }, 300);

    return () => {
      cancelled = true;
      clearTimeout(handle);
    };
  }, [query]);

  return (
    <div className="min-h-screen bg-bg">
      <AppHeader />
      <main className="mx-auto max-w-2xl px-4 py-16">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold">Find a ticker</h1>
          <p className="mt-2 text-muted">
            Search for a symbol to open its live prediction dashboard.
          </p>
        </div>

        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted" />
          <input
            className="input py-3 pl-11 text-base"
            placeholder="Search e.g. AAPL, Tesla, MSFT…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
          />
        </div>

        <div className="mt-4">
          {loading && <div className="px-2 py-3 text-sm text-muted">Searching…</div>}
          {error && <div className="px-2 py-3 text-sm text-bad">{error}</div>}

          {!loading && !error && results.length === 0 && query.trim() && (
            <div className="px-2 py-3 text-sm text-muted">No matches.</div>
          )}

          <ul className="divide-y divide-line overflow-hidden rounded-xl border border-line">
            {results.map((r) => (
              <li key={r.symbol}>
                <button
                  className="flex w-full items-center justify-between gap-3 bg-bg-card px-4 py-3 text-left transition-colors hover:bg-bg-soft"
                  onClick={() => navigate(`/dashboard/${encodeURIComponent(r.symbol)}`)}
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent/10 text-accent">
                      <TrendingUp className="h-4 w-4" />
                    </div>
                    <div>
                      <div className="font-semibold">{r.displaySymbol || r.symbol}</div>
                      <div className="text-xs text-muted">{r.description}</div>
                    </div>
                  </div>
                  <span className="rounded-md bg-bg-soft px-2 py-0.5 text-[11px] text-muted">
                    {r.type}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      </main>
    </div>
  );
}
