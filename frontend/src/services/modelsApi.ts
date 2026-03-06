// ─────────────────────────────────────────────────────────────────────────────
// services/modelsApi.ts
// API client for ML model metadata and predictions.
// ─────────────────────────────────────────────────────────────────────────────

// ── URL resolution (mirrors aiAnalysis.ts) ────────────────────────────────────

function getApiBase(): string {
  const win = window as unknown as { __CHECKDK_ENV__?: { CHECKDK_API_URL?: string } };
  if (win.__CHECKDK_ENV__?.CHECKDK_API_URL) {
    return win.__CHECKDK_ENV__.CHECKDK_API_URL.replace(/\/+$/, '');
  }
  if (import.meta.env.VITE_API_URL) {
    return (import.meta.env.VITE_API_URL as string).replace(/\/+$/, '');
  }
  return '/api';
}

// ── Types ─────────────────────────────────────────────────────────────────────

export interface FeatureImportance {
  feature: string;
  importance: number;
}

export interface ModelMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  roc_auc: number;
  confusion_matrix: [[number, number], [number, number]];
  feature_importances?: FeatureImportance[] | null;
}

export interface ModelInfo {
  key: string;
  display_name: string;
  algorithm: string;
  trained: boolean;
  trained_at?: string | null;
  metrics?: ModelMetrics | null;
}

export interface ModelsResponse {
  models: ModelInfo[];
}

export interface PodMetricsInput {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_latency: number;
  restart_count: number;
  probe_failures: number;
  node_cpu_pressure: number;
  node_memory_pressure: number;
  pod_age_minutes: number;
}

export interface ModelPredictionResult {
  model: string;
  prediction: number;
  label: 'healthy' | 'failure';
  confidence: number;
}

// ── API calls ─────────────────────────────────────────────────────────────────

export async function fetchModels(): Promise<ModelsResponse> {
  const res = await fetch(`${getApiBase()}/models`);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Failed to load models (${res.status}): ${body}`);
  }
  return res.json() as Promise<ModelsResponse>;
}

export async function predictWithModel(
  modelKey: string,
  metrics: PodMetricsInput,
): Promise<ModelPredictionResult> {
  const res = await fetch(`${getApiBase()}/models/predict/${modelKey}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(metrics),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Prediction failed (${res.status}): ${body}`);
  }
  return res.json() as Promise<ModelPredictionResult>;
}
