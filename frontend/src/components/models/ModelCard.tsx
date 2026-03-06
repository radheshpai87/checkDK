// ─────────────────────────────────────────────────────────────────────────────
// components/models/ModelCard.tsx
// Displays a single ML model's name, algorithm, training status and key metrics.
// ─────────────────────────────────────────────────────────────────────────────

import type { ModelInfo } from '../../services/modelsApi';

interface ModelCardProps {
  model: ModelInfo;
  isSelected: boolean;
  onClick: () => void;
}

const MODEL_COLORS: Record<string, { accent: string; dot: string; bg: string }> = {
  random_forest: {
    accent: 'border-emerald-500/40 hover:border-emerald-500/70',
    dot: 'bg-emerald-400',
    bg: 'bg-emerald-500/10',
  },
  xgboost: {
    accent: 'border-violet-500/40 hover:border-violet-500/70',
    dot: 'bg-violet-400',
    bg: 'bg-violet-500/10',
  },
  lstm: {
    accent: 'border-sky-500/40 hover:border-sky-500/70',
    dot: 'bg-sky-400',
    bg: 'bg-sky-500/10',
  },
};

const DEFAULT_COLORS = {
  accent: 'border-slate-700 hover:border-slate-500',
  dot: 'bg-slate-400',
  bg: 'bg-slate-800',
};

function MetricChip({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex flex-col items-center gap-0.5 px-3 py-2 rounded-lg bg-slate-800/80 border border-slate-700/60">
      <span className="text-slate-300 text-sm font-mono font-bold">
        {(value * 100).toFixed(1)}%
      </span>
      <span className="text-slate-500 text-[10px] font-mono uppercase tracking-wider">
        {label}
      </span>
    </div>
  );
}

export default function ModelCard({ model, isSelected, onClick }: ModelCardProps) {
  const colors = MODEL_COLORS[model.key] ?? DEFAULT_COLORS;
  const selectedRing = isSelected ? 'ring-2 ring-indigo-500/50' : '';

  return (
    <button
      onClick={onClick}
      className={`w-full text-left p-5 rounded-2xl bg-slate-900 border transition-all duration-200 cursor-pointer ${colors.accent} ${selectedRing}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="flex items-center gap-2.5">
          <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${colors.dot} ${model.trained ? 'animate-none' : 'opacity-30'}`} />
          <div>
            <h3 className="text-white font-semibold text-base leading-tight">
              {model.display_name}
            </h3>
            <p className="text-slate-500 text-xs font-mono mt-0.5 leading-tight">
              {model.algorithm}
            </p>
          </div>
        </div>

        {/* Status pill */}
        {model.trained ? (
          <span className="flex-shrink-0 px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[10px] font-mono font-semibold">
            TRAINED
          </span>
        ) : (
          <span className="flex-shrink-0 px-2 py-0.5 rounded-md bg-slate-800 border border-slate-700 text-slate-500 text-[10px] font-mono font-semibold">
            NOT TRAINED
          </span>
        )}
      </div>

      {/* Metrics row */}
      {model.trained && model.metrics ? (
        <div className="flex gap-2">
          <MetricChip label="Accuracy" value={model.metrics.accuracy} />
          <MetricChip label="F1" value={model.metrics.f1} />
          <MetricChip label="ROC-AUC" value={model.metrics.roc_auc} />
        </div>
      ) : (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-slate-800/60 border border-slate-700/40">
          <svg className="w-4 h-4 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
          </svg>
          <span className="text-slate-600 text-xs font-mono">
            Run <code className="text-slate-500">python train_all.py</code> to train this model
          </span>
        </div>
      )}

      {/* Trained at */}
      {model.trained_at && (
        <p className="mt-3 text-slate-600 text-[10px] font-mono">
          Trained {new Date(model.trained_at).toLocaleString()}
        </p>
      )}
    </button>
  );
}
