import { Link, useNavigate } from 'react-router-dom';
import { LineChart, LogOut, Search as SearchIcon } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { cn, fmtPrice } from '../lib/utils';

interface AppHeaderProps {
  ticker?: string;
  price?: number | null;
  source?: 'live' | 'replay' | null;
}

export function AppHeader({ ticker, price, source }: AppHeaderProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function onLogout() {
    await logout();
    navigate('/login', { replace: true });
  }

  return (
    <header className="sticky top-0 z-10 border-b border-line bg-bg/80 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3">
        <div className="flex items-center gap-4">
          <Link to="/" className="flex items-center gap-2">
            <LineChart className="h-5 w-5 text-accent" />
            <span className="font-bold">StockSense</span>
          </Link>

          {ticker && (
            <div className="flex items-center gap-3 border-l border-line pl-4">
              <span className="text-lg font-bold tracking-tight">{ticker}</span>
              {price != null && (
                <span className="font-mono text-lg tabular-nums text-accent">
                  ${fmtPrice(price)}
                </span>
              )}
              {source && (
                <span
                  className={cn(
                    'rounded-md px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide',
                    source === 'live'
                      ? 'bg-good/15 text-good'
                      : 'bg-warn/15 text-warn',
                  )}
                >
                  {source}
                </span>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          {ticker && (
            <Link to="/" className="btn-ghost px-3 py-1.5 text-xs">
              <SearchIcon className="h-3.5 w-3.5" />
              Search
            </Link>
          )}
          {user && <span className="hidden text-sm text-muted sm:inline">{user.username}</span>}
          <button onClick={onLogout} className="btn-ghost px-3 py-1.5 text-xs">
            <LogOut className="h-3.5 w-3.5" />
            Logout
          </button>
        </div>
      </div>
    </header>
  );
}
