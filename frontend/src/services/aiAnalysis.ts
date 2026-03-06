// ─────────────────────────────────────────────────────────────────────────────
// services/aiAnalysis.ts
// Proxies config audit requests to the checkDK backend API.
// No LLM SDKs are imported – all inference runs server-side.
//
// Auth-aware: when a JWT token is supplied, calls the real backend with a
// Bearer header. Without a token, delegates to the local rule-based analyzer.
// ─────────────────────────────────────────────────────────────────────────────

import { mockAnalyze } from '../lib/mockAnalyzer';

export type IssueSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type AnalysisStatus = 'secure' | 'warning' | 'critical';

export interface AnalysisIssue {
  severity: IssueSeverity;
  title: string;
  description: string;
  line?: number | null;
  recommendation?: string;
  suggestion?: string;
  category?: string | null;
}

export interface AnalysisHighlight {
  type?: 'good' | 'bad' | 'neutral';
  title?: string;
  text?: string;
  description?: string;
}

export interface AnalysisResult {
  score: number;            // 0–100
  status: AnalysisStatus | string;
  summary: string;
  issues: AnalysisIssue[];
  highlights: AnalysisHighlight[];
  provider?: string;        // internal provider identifier, not shown in UI
}

// ── API URL resolution ────────────────────────────────────────────────────────

function getApiBase(): string {
  // 1. Runtime injection (production containers)
  const win = window as unknown as { __CHECKDK_ENV__?: { CHECKDK_API_URL?: string } };
  if (win.__CHECKDK_ENV__?.CHECKDK_API_URL) {
    return win.__CHECKDK_ENV__.CHECKDK_API_URL.replace(/\/+$/, '');
  }

  // 2. Vite build-time env (local dev override)
  if (import.meta.env.VITE_API_URL) {
    return (import.meta.env.VITE_API_URL as string).replace(/\/+$/, '');
  }

  // 3. In dev mode, use the Vite proxy path so requests stay same-origin
  //    (vite.config.ts rewrites /api/* → http://localhost:8000/*)
  if (import.meta.env.DEV) {
    return '/api';
  }

  // 4. Production fallback — use the nginx /api proxy path.
  //    Never return a Docker-internal hostname (backend:8000); the browser
  //    can't resolve it — only nginx can.
  return '/api';
}

// ── Main export ───────────────────────────────────────────────────────────────

/**
 * Analyse a config file.
 *
 * - With `token`: calls the real backend `/analyze/playground` endpoint with
 *   full AI-powered analysis (Bearer token in Authorization header).
 * - Without `token`: runs the local rule-based analyzer instantly with no
 *   network requests.
 */
export async function analyze(
  configContent: string,
  filename?: string,
  token?: string | null,
): Promise<AnalysisResult> {
  // Unauthenticated → local rule-based analysis only
  if (!token) {
    return mockAnalyze(configContent);
  }

  // Authenticated → full backend AI analysis
  const url = `${getApiBase()}/analyze/playground`;

  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ content: configContent, filename }),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Backend returned ${res.status}: ${body}`);
  }

  const result = (await res.json()) as AnalysisResult;
  // Debug: log which provider handled the request
  console.debug('[CheckDK] analysis provider:', result.provider ?? 'unknown');
  return result;
}
