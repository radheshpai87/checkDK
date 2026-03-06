// ─────────────────────────────────────────────────────────────────────────────
// components/models/MetricsComparisonChart.tsx
// SVG grouped bar chart comparing Accuracy, F1, and ROC-AUC across all models.
// ─────────────────────────────────────────────────────────────────────────────

import type { ModelInfo } from '../../services/modelsApi';

interface MetricsComparisonChartProps {
  models: ModelInfo[];
}

const METRIC_KEYS: { key: 'accuracy' | 'f1' | 'roc_auc'; label: string }[] = [
  { key: 'accuracy', label: 'Accuracy' },
  { key: 'f1', label: 'F1 Score' },
  { key: 'roc_auc', label: 'ROC-AUC' },
];

const MODEL_COLORS: Record<string, string> = {
  random_forest: '#34d399', // emerald-400
  xgboost: '#a78bfa',       // violet-400
  lstm: '#38bdf8',          // sky-400
};

const FALLBACK_COLORS = ['#34d399', '#a78bfa', '#38bdf8'];

export default function MetricsComparisonChart({ models }: MetricsComparisonChartProps) {
  const trained = models.filter((m) => m.trained && m.metrics);

  if (trained.length === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-slate-600 text-sm font-mono">
        No trained models to compare yet.
      </div>
    );
  }

  // Chart dimensions
  const chartWidth = 600;
  const chartHeight = 200;
  const paddingLeft = 32;
  const paddingBottom = 28;
  const paddingTop = 12;
  const paddingRight = 16;

  const plotWidth = chartWidth - paddingLeft - paddingRight;
  const plotHeight = chartHeight - paddingTop - paddingBottom;

  const numGroups = METRIC_KEYS.length; // 3 metric groups
  const numBars = trained.length;
  const groupWidth = plotWidth / numGroups;
  const barPad = 4;
  const barWidth = Math.min(28, (groupWidth - barPad * (numBars + 1)) / numBars);

  return (
    <div className="w-full">
      {/* Legend */}
      <div className="flex flex-wrap gap-4 mb-4">
        {trained.map((m, i) => (
          <div key={m.key} className="flex items-center gap-1.5">
            <span
              className="w-3 h-3 rounded-sm flex-shrink-0"
              style={{ backgroundColor: MODEL_COLORS[m.key] ?? FALLBACK_COLORS[i] }}
            />
            <span className="text-slate-400 text-xs font-mono">{m.display_name}</span>
          </div>
        ))}
      </div>

      {/* SVG chart */}
      <svg
        viewBox={`0 0 ${chartWidth} ${chartHeight}`}
        className="w-full"
        aria-label="Model metrics comparison chart"
      >
        {/* Y-axis grid lines at 25%, 50%, 75%, 100% */}
        {[0.25, 0.5, 0.75, 1.0].map((pct) => {
          const y = paddingTop + plotHeight * (1 - pct);
          return (
            <g key={pct}>
              <line
                x1={paddingLeft}
                y1={y}
                x2={paddingLeft + plotWidth}
                y2={y}
                stroke="#1e293b"
                strokeWidth={1}
              />
              <text
                x={paddingLeft - 4}
                y={y + 4}
                textAnchor="end"
                fontSize={9}
                fill="#475569"
                fontFamily="monospace"
              >
                {(pct * 100).toFixed(0)}
              </text>
            </g>
          );
        })}

        {/* Bars */}
        {METRIC_KEYS.map((metric, gi) => {
          const groupX = paddingLeft + gi * groupWidth;
          const totalBarWidth = numBars * barWidth + (numBars - 1) * barPad;
          const startX = groupX + (groupWidth - totalBarWidth) / 2;

          return (
            <g key={metric.key}>
              {trained.map((model, bi) => {
                const value = model.metrics![metric.key] ?? 0;
                const barH = plotHeight * value;
                const x = startX + bi * (barWidth + barPad);
                const y = paddingTop + plotHeight - barH;
                const color = MODEL_COLORS[model.key] ?? FALLBACK_COLORS[bi];

                return (
                  <g key={model.key}>
                    <rect
                      x={x}
                      y={y}
                      width={barWidth}
                      height={barH}
                      rx={3}
                      fill={color}
                      fillOpacity={0.85}
                    />
                    {/* Value label on top */}
                    <text
                      x={x + barWidth / 2}
                      y={y - 3}
                      textAnchor="middle"
                      fontSize={8}
                      fill={color}
                      fontFamily="monospace"
                    >
                      {(value * 100).toFixed(1)}
                    </text>
                  </g>
                );
              })}

              {/* X-axis label */}
              <text
                x={groupX + groupWidth / 2}
                y={chartHeight - 6}
                textAnchor="middle"
                fontSize={10}
                fill="#64748b"
                fontFamily="sans-serif"
              >
                {metric.label}
              </text>
            </g>
          );
        })}

        {/* X axis baseline */}
        <line
          x1={paddingLeft}
          y1={paddingTop + plotHeight}
          x2={paddingLeft + plotWidth}
          y2={paddingTop + plotHeight}
          stroke="#334155"
          strokeWidth={1}
        />
      </svg>
    </div>
  );
}
