/**
 * checkDK API client
 *
 * Usage:
 *   import { analyzeDockerCompose, analyzeKubernetes, predictPodHealth } from '@/lib/api'
 *
 * The base URL is controlled by the VITE_API_URL env variable.
 * In development (without Docker) it falls back to http://localhost:8000
 * so the Vite dev server proxy in vite.config.ts forwards /api/* calls.
 */

// Resolve the API base URL at runtime:
//  1. Runtime injection from env.sh via window.__CHECKDK_ENV__ (Docker)
//  2. Vite build-time env var (local dev with explicit override)
//  3. /api — nginx proxy path (Docker production, same-origin)
const _env = (window as unknown as { __CHECKDK_ENV__?: { CHECKDK_API_URL?: string } }).__CHECKDK_ENV__
const API_BASE = (
  _env?.CHECKDK_API_URL ||
  import.meta.env.VITE_API_URL ||
  '/api'
).replace(/\/+$/, '')

// ── Shared types ──────────────────────────────────────────────────────────────

export type Severity = 'critical' | 'warning' | 'info'

export interface Issue {
  type: string
  severity: Severity
  message: string
  file_path?: string
  line_number?: number
  service_name?: string
  details?: Record<string, unknown>
}

export interface Fix {
  description: string
  steps: string[]
  code_snippet?: string
  auto_applicable?: boolean
  explanation?: string
  root_cause?: string
}

export interface AnalysisResult {
  success: boolean
  issues: Issue[]
  fixes: Fix[]
  warnings: string[]
}

// ── Predict types ─────────────────────────────────────────────────────────────

export interface PredictRequest {
  cpu: number
  memory: number
  disk?: number
  latency?: number
  restarts?: number
  probe_failures?: number
  cpu_pressure?: number
  mem_pressure?: number
  age?: number
  service?: string
  platform?: 'docker' | 'kubernetes'
  no_ai?: boolean
}

export interface MLPrediction {
  label: string
  confidence: number
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  is_failure: boolean
}

export interface LLMAssessment {
  assessment: string
  root_cause: string
  recommendations: string[]
}

export interface PredictResponse {
  prediction: MLPrediction
  assessment?: LLMAssessment
}

// ── Health ────────────────────────────────────────────────────────────────────

export async function apiHealth(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/health`)
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`)
  return res.json()
}

// ── Analysis ──────────────────────────────────────────────────────────────────

/**
 * Analyse a Docker Compose YAML string.
 * @param content  Raw YAML text (e.g. read from a file input or a textarea)
 */
export async function analyzeDockerCompose(content: string): Promise<AnalysisResult> {
  const res = await fetch(`${API_BASE}/analyze/docker-compose`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`Docker Compose analysis failed (${res.status}): ${detail}`)
  }
  return res.json()
}

/**
 * Analyse a Kubernetes manifest YAML string.
 * @param content  Raw YAML text (supports multi-document --- separators)
 */
export async function analyzeKubernetes(content: string): Promise<AnalysisResult> {
  const res = await fetch(`${API_BASE}/analyze/kubernetes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`Kubernetes analysis failed (${res.status}): ${detail}`)
  }
  return res.json()
}

// ── User history & patterns ───────────────────────────────────────────────────

export interface HistoryItem {
  id: string
  analysisId?: string
  configType: string
  filename: string
  score: number
  status: string
  issueCount: number
  topCategories: string[]
  createdAt: string
  analyzedAt?: string
  summary?: string
  aiProvider?: string
}

export interface PatternItem {
  category: string
  label: string
  count: number
}

function authHeaders(token: string): HeadersInit {
  return { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }
}

export async function fetchUserHistory(token: string): Promise<HistoryItem[]> {
  const res = await fetch(`${API_BASE}/user/history`, { headers: authHeaders(token) })
  if (!res.ok) throw new Error(`Failed to load history (${res.status})`)
  const data = await res.json()
  // Normalize backend snake_case / alternate field names to what the UI expects
  return (data.history as Record<string, unknown>[]).map((h) => ({
    id: (h.id ?? h.analysisId) as string,
    analysisId: h.analysisId as string | undefined,
    configType: h.configType as string,
    filename: h.filename as string,
    score: h.score as number,
    status: h.status as string,
    issueCount: h.issueCount as number,
    topCategories: (h.topCategories ?? []) as string[],
    createdAt: (h.createdAt ?? h.analyzedAt) as string,
    analyzedAt: h.analyzedAt as string | undefined,
    summary: h.summary as string | undefined,
    aiProvider: h.aiProvider as string | undefined,
  }))
}

export async function fetchUserPatterns(token: string): Promise<PatternItem[]> {
  const res = await fetch(`${API_BASE}/user/patterns`, { headers: authHeaders(token) })
  if (!res.ok) throw new Error(`Failed to load patterns (${res.status})`)
  const data = await res.json()
  return data.patterns as PatternItem[]
}

// ── Pod health prediction ─────────────────────────────────────────────────────

/**
 * Run the Random Forest model and (optionally) LLM against pod runtime metrics.
 */
export async function predictPodHealth(metrics: PredictRequest): Promise<PredictResponse> {
  const res = await fetch(`${API_BASE}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(metrics),
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`Pod health prediction failed (${res.status}): ${detail}`)
  }
  return res.json()
}
