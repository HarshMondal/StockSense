import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import type { ReactNode } from 'react';
import { api, ApiError } from '../lib/api';
import type { User } from '../types';

type AuthStatus = 'loading' | 'authenticated' | 'anonymous';

interface AuthContextValue {
  user: User | null;
  status: AuthStatus;
  login: (username: string, password: string) => Promise<void>;
  signup: (username: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthStatus>('loading');

  const bootstrap = useCallback(async () => {
    // Seed CSRF cookie first so the first mutating request never 403s.
    await api.ensureCsrf();
    try {
      const me = await api.me();
      setUser(me);
      setStatus('authenticated');
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setUser(null);
        setStatus('anonymous');
      } else {
        // Network/server error: treat as anonymous so the app still renders.
        setUser(null);
        setStatus('anonymous');
      }
    }
  }, []);

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  const login = useCallback(async (username: string, password: string) => {
    await api.ensureCsrf();
    const me = await api.login(username, password);
    setUser(me);
    setStatus('authenticated');
  }, []);

  const signup = useCallback(
    async (username: string, email: string, password: string) => {
      await api.ensureCsrf();
      const me = await api.signup(username, email, password);
      setUser(me);
      setStatus('authenticated');
    },
    [],
  );

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } finally {
      setUser(null);
      setStatus('anonymous');
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, status, login, signup, logout, refresh: bootstrap }),
    [user, status, login, signup, logout, bootstrap],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
