// ─────────────────────────────────────────────────────────────────────────────
// components/models/PredictionWidget.tsx
// Live pod failure prediction form using the ml-models inference service.
// ─────────────────────────────────────────────────────────────────────────────

import { useState } from 'react';
import { predictWithModel, type PodMetricsInput, type ModelPredictionResult } from '../../services/modelsApi';

interface PredictionWidgetProps {
  availableModels: { key: string; display_name: string }[];
  token: string;
}

const DEFAULT_METRICS: PodMetricsInput = {
  cpu_usage: 45,
  memory_usage: 60,
  disk_usage: 30,
  network_latency: 10,
  restart_count: 0,
  probe_failures: 0,
  node_cpu_pressure: 0,
  node_memory_pressure: 0,
  pod_age_minutes: 120,
};

type FieldDef = {
  key: keyof PodMetricsInput;
  label: string;
  unit: string;
  min: number;
  max: number;
  step: number;
  isFloat: boolean;
};

const FIELDS: FieldDef[] = [
  { key: 'cpu_usage',           label: 'CPU Usage',           unit: '%',   min: 0, max: 100,  step: 1,    isFloat: true },
  { key: 'memory_usage',        label: 'Memory Usage',        unit: '%',   min: 0, max: 100,  step: 1,    isFloat: true },
  { key: 'disk_usage',          label: 'Disk Usage',          unit: '%',   min: 0, max: 100,  step: 1,    isFloat: true },
  { key: 'network_latency',     label: 'Network Latency',     unit: 'ms',  min: 0, max: 5000, step: 1,    isFloat: true },
  { key: 'restart_count',       label: 'Restart Count',       unit: '',    min: 0, max: 100,  step: 1,    isFloat: false },
  { key: 'probe_failures',      label: 'Probe Failures',      unit: '',    min: 0, max: 100,  step: 1,    isFloat: false },
  { key: 'node_cpu_pressure',   label: 'Node CPU Pressure',   unit: '0/1', min: 0, max: 1,    step: 1,    isFloat: false },
  { key: 'node_memory_pressure',label: 'Node Memory Pressure',unit: '0/1', min: 0, max: 1,    step: 1,    isFloat: false },
  { key: 'pod_age_minutes',     label: 'Pod Age',             unit: 'min', min: 0, max: 100000, step: 1,  isFloat: false },
];

// Styling is driven by P(failure), NOT the binary label.
// This avoids the bucket where label='healthy' but risk is still 43% — showing green would be misleading.
type RiskTier = 'critical' | 'high' | 'medium' | 'low';

function getRiskTier(failureProb: number): RiskTier {
  if (failureProb >= 0.75) return 'critical';
  if (failureProb >= 0.5)  return 'high';
  if (failureProb >= 0.25) return 'medium';
  return 'low';
}

const RISK_STYLES: Record<RiskTier, { border: string; text: string; bg: string; barColor: string; riskLabel: string }> = {
  critical: { border: 'border-red-500/50',    text: 'text-red-300',    bg: 'bg-red-500/10',    barColor: '#f87171', riskLabel: 'Critical' },
  high:     { border: 'border-orange-500/50', text: 'text-orange-300', bg: 'bg-orange-500/10', barColor: '#fb923c', riskLabel: 'High' },
  medium:   { border: 'border-amber-500/50',  text: 'text-amber-300',  bg: 'bg-amber-500/10',  barColor: '#facc15', riskLabel: 'Medium' },
  low:      { border: 'border-emerald-500/40',text: 'text-emerald-300',bg: 'bg-emerald-500/10',barColor: '#34d399', riskLabel: 'Low' },
};

export default function PredictionWidget({ availableModels, token }: PredictionWidgetProps) {
  const [selectedModel, setSelectedModel] = useState(availableModels[0]?.key ?? 'random_forest');
  const [metrics, setMetrics] = useState<PodMetricsInput>(DEFAULT_METRICS);
  const [result, setResult] = useState<ModelPredictionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (key: keyof PodMetricsInput, raw: string, isFloat: boolean) => {
    const val = isFloat ? parseFloat(raw) : parseInt(raw, 10);
    if (!isNaN(val)) {
      setMetrics((prev) => ({ ...prev, [key]: val }));
    }
  };

  const handlePreset = (preset: 'healthy' | 'stressed') => {
    if (preset === 'healthy') {
      setMetrics(DEFAULT_METRICS);
    } else {
      setMetrics({
        cpu_usage: 94,
        memory_usage: 92,
        disk_usage: 88,
        network_latency: 450,
        restart_count: 7,
        probe_failures: 4,
        node_cpu_pressure: 1,
        node_memory_pressure: 1,
        pod_age_minutes: 8,
      });
    }
    setResult(null);
    setError(null);
  };

  const handlePredict = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await predictWithModel(selectedModel, metrics, token);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Prediction failed.');
    } finally {
      setLoading(false);
    }
  };

  // Derive all result display values outside JSX — no IIFE anti-pattern
  const failureProb = result ? result.confidence : 0;
  const riskTier = result ? getRiskTier(failureProb) : null;
  const riskStyles = riskTier ? RISK_STYLES[riskTier] : null;
  // Label confidence = model's certainty in its own binary prediction
  const labelConfidence = result
    ? (result.label === 'failure' ? failureProb : 1 - failureProb)
    : 0;

  return (
    <div className="space-y-5">
      {/* Model selector + presets */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <label className="text-slate-400 text-xs font-mono">Model:</label>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-sm font-mono focus:outline-none focus:border-indigo-500"
          >
            {availableModels.map((m) => (
              <option key={m.key} value={m.key}>{m.display_name}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2 ml-auto">
          <span className="text-slate-500 text-xs font-mono">Presets:</span>
          <button
            onClick={() => handlePreset('healthy')}
            className="px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono hover:bg-emerald-500/20 transition-colors"
          >
            Healthy pod
          </button>
          <button
            onClick={() => handlePreset('stressed')}
            className="px-2.5 py-1 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-mono hover:bg-red-500/20 transition-colors"
          >
            Stressed pod
          </button>
        </div>
      </div>

      {/* Input grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {FIELDS.map((field) => (
          <div key={field.key} className="flex flex-col gap-1">
            <label className="text-slate-500 text-[10px] font-mono uppercase tracking-wider">
              {field.label}
              {field.unit && <span className="ml-1 text-slate-600">({field.unit})</span>}
            </label>
            <input
              type="number"
              min={field.min}
              max={field.max}
              step={field.step}
              value={metrics[field.key]}
              onChange={(e) => handleChange(field.key, e.target.value, field.isFloat)}
              className="px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-sm font-mono focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/30 w-full"
            />
          </div>
        ))}
      </div>

      {/* Predict button */}
      <button
        onClick={handlePredict}
        disabled={loading || availableModels.length === 0}
        className="w-full py-2.5 rounded-xl bg-indigo-500 hover:bg-indigo-400 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold text-sm transition-colors flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Running Model…
          </>
        ) : (
          'Run Prediction'
        )}
      </button>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-2 p-3 rounded-xl bg-red-500/10 border border-red-500/30">
          <svg className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
          <p className="text-red-300 text-sm">{error}</p>
        </div>
      )}

      {/* Result — card color driven by P(failure) risk tier, not binary label */}
      {result && riskStyles && (
        <div className={`p-4 rounded-xl border ${riskStyles.border} ${riskStyles.bg} space-y-4`}>
          {/* Top row: label + label confidence */}
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              {/* Colored status dot instead of emoji */}
              <span
                className="w-3 h-3 rounded-full flex-shrink-0"
                style={{ backgroundColor: riskStyles.barColor }}
              />
              <div>
                <p className={`font-bold text-lg capitalize ${riskStyles.text}`}>
                  {result.label}
                  <span className="ml-2 text-xs font-normal opacity-70">
                    — {riskStyles.riskLabel} risk
                  </span>
                </p>
                <p className="text-slate-400 text-xs font-mono">
                  via {availableModels.find((m) => m.key === result.model)?.display_name ?? result.model}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className={`text-2xl font-mono font-bold ${riskStyles.text}`}>
                {(labelConfidence * 100).toFixed(1)}%
              </p>
              <p className="text-slate-500 text-xs font-mono">prediction confidence</p>
            </div>
          </div>

          {/* Prediction confidence bar */}
          <div>
            <div className="flex justify-between text-[10px] font-mono text-slate-500 mb-1">
              <span>Confidence in prediction</span>
              <span className={riskStyles.text}>{(labelConfidence * 100).toFixed(1)}%</span>
            </div>
            <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{ width: `${labelConfidence * 100}%`, backgroundColor: riskStyles.barColor }}
              />
            </div>
          </div>

          {/* Failure probability bar — always shows raw P(failure) */}
          <div>
            <div className="flex justify-between text-[10px] font-mono text-slate-500 mb-1">
              <span>Failure probability P(failure)</span>
              <span style={{ color: riskStyles.barColor }}>
                {(failureProb * 100).toFixed(1)}% — {riskStyles.riskLabel}
              </span>
            </div>
            <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{ width: `${failureProb * 100}%`, backgroundColor: riskStyles.barColor }}
              />
            </div>
          </div>
        </div>
      )}

      {availableModels.length === 0 && (
        <p className="text-center text-slate-600 text-sm font-mono py-4">
          Train at least one model to enable predictions.
        </p>
      )}
    </div>
  );
}
