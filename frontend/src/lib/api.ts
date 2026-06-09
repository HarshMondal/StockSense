import type {
  AccuracyResponse,
  HistoryResponse,
  Horizon,
  SearchResponse,
  Snapshot,
  User,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(status: number, message: string, data: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

function readCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp('(^|;\\s*)' + name + '=([^;]*)'));
  return match ? decodeURIComponent(match[2]) : null;
}

async function parseBody(res: Response): Promise<unknown> {
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
}

/**
 * Core fetch wrapper: always sends cookies; for mutating requests it ensures the
 * CSRF cookie exists and forwards it via the X-CSRFToken header.
 */
async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const method = opts.method ?? 'GET';
  const headers: Record<string, string> = {};

  if (method !== 'GET' && method !== 'HEAD') {
    if (!readCookie('csrftoken')) {
      await ensureCsrf();
    }
    const token = readCookie('csrftoken');
    if (token) headers['X-CSRFToken'] = token;
  }

  let body: string | undefined;
  if (opts.body !== undefined) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(opts.body);
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    credentials: 'include',
    headers,
    body,
  });

  const data = await parseBody(res);
  if (!res.ok) {
    const message =
      (data && typeof data === 'object' && 'detail' in data && typeof data.detail === 'string'
        ? data.detail
        : `Request failed (${res.status})`) || `Request failed (${res.status})`;
    throw new ApiError(res.status, message, data);
  }
  return data as T;
}

let csrfPromise: Promise<void> | null = null;

/** Fetch /api/auth/csrf/ once to seed the csrftoken cookie. */
export function ensureCsrf(): Promise<void> {
  if (!csrfPromise) {
    csrfPromise = fetch(`${API_BASE}/api/auth/csrf/`, {
      credentials: 'include',
    })
      .then(() => undefined)
      .catch(() => {
        csrfPromise = null;
      });
  }
  return csrfPromise;
}

export const api = {
  ensureCsrf,

  me: () => request<User>('/api/auth/me/'),

  login: (username: string, password: string) =>
    request<User>('/api/auth/login/', { method: 'POST', body: { username, password } }),

  signup: (username: string, email: string, password: string) =>
    request<User>('/api/auth/signup/', {
      method: 'POST',
      body: { username, email, password },
    }),

  logout: () => request<unknown>('/api/auth/logout/', { method: 'POST' }),

  search: (q: string) => request<SearchResponse>(`/api/search/?q=${encodeURIComponent(q)}`),

  snapshot: (ticker: string) => request<Snapshot>(`/api/market/${encodeURIComponent(ticker)}/snapshot/`),

  accuracy: (ticker: string, horizon: Horizon) =>
    request<AccuracyResponse>(
      `/api/predictions/${encodeURIComponent(ticker)}/${horizon}/accuracy/`,
    ),

  history: (ticker: string, horizon: Horizon, limit = 120) =>
    request<HistoryResponse>(
      `/api/predictions/${encodeURIComponent(ticker)}/${horizon}/history/?limit=${limit}`,
    ),
};

export { API_BASE };
