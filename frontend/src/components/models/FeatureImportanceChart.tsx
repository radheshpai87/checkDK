// ─────────────────────────────────────────────────────────────────────────────
// components/models/FeatureImportanceChart.tsx
// Horizontal bar chart for feature importances (RF & XGBoost only).
// ─────────────────────────────────────────────────────────────────────────────

import type { FeatureImportance } from '../../services/modelsApi';

interface FeatureImportanceChartProps {
  importances: FeatureImportance[];
  color?: string;
}

const FEATURE_LABELS: Record<string, string> = {
  cpu_usage: 'CPU Usage',
  memory_usage: 'Memory Usage',
  disk_usage: 'Disk Usage',
  network_latency: 'Network Latency',
  restart_count: 'Restart Count',
  probe_failures: 'Probe Failures',
  node_cpu_pressure: 'Node CPU Pressure',
  node_memory_pressure: 'Node Memory Pressure',
  pod_age_minutes: 'Pod Age (min)',
};

export default function FeatureImportanceChart({
  importances,
  color = '#a78bfa',
}: FeatureImportanceChartProps) {
  if (!importances || importances.length === 0) {
    return (
      <p className="text-slate-600 text-xs font-mono py-2">
        Feature importances not available for this model.
      </p>
    );
  }

  // Already sorted descending by train.py
  const max = importances[0].importance;

  return (
    <div className="space-y-2">
      {importances.map(({ feature, importance }) => {
        const pct = max > 0 ? (importance / max) * 100 : 0;
        const label = FEATURE_LABELS[feature] ?? feature;

        return (
          <div key={feature} className="flex items-center gap-2">
            {/* Feature name */}
            <span className="w-36 flex-shrink-0 text-slate-400 text-xs font-mono text-right truncate">
              {label}
            </span>

            {/* Bar track */}
            <div className="flex-1 h-4 rounded bg-slate-800 overflow-hidden">
              <div
                className="h-full rounded transition-all duration-500"
                style={{
                  width: `${pct}%`,
                  backgroundColor: color,
                  opacity: 0.8,
                }}
              />
            </div>

            {/* Value */}
            <span className="w-12 flex-shrink-0 text-right text-xs font-mono"
              style={{ color }}
            >
              {(importance * 100).toFixed(1)}%
            </span>
          </div>
        );
      })}
    </div>
  );
}
