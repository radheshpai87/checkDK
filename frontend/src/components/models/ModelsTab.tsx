// ─────────────────────────────────────────────────────────────────────────────
// components/models/ModelsTab.tsx
// Dashboard tab that shows ML model cards, metrics comparison, feature
// importances, and a live prediction widget.
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useEffect } from 'react';
import { fetchModels, type ModelInfo, type ModelMetrics } from '../../services/modelsApi';
import ModelCard from './ModelCard';
import MetricsComparisonChart from './MetricsComparisonChart';
import FeatureImportanceChart from './FeatureImportanceChart';
import PredictionWidget from './PredictionWidget';

const MODEL_COLORS: Record<string, string> = {
  random_forest: '#34d399',
  xgboost: '#a78bfa',
  lstm: '#38bdf8',
};

export default function ModelsTab() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<ModelInfo | null>(null);
  const [showFeatureImportance, setShowFeatureImportance] = useState(false);

  useEffect(() => {
    fetchModels()
      .then((data) => {
        setModels(data.models);
        // Pre-select first trained model
        const firstTrained = data.models.find((m) => m.trained);
        if (firstTrained) setSelectedModel(firstTrained);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to load models.');
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24 gap-3 text-slate-500">
        <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <span className="text-sm font-mono">Loading models…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-12 px-4 text-center max-w-xl mx-auto">
        <div className="flex items-start gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm text-left">
          <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
          <div>
            <p className="font-semibold mb-1">Failed to load model metadata</p>
            <p className="text-red-400 text-xs font-mono">{error}</p>
            <p className="text-slate-500 text-xs mt-2">
              Make sure the backend and ml-models services are running, and models have been trained.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const trainedModels = models.filter((m) => m.trained && m.metrics);
  const availableForPrediction = trainedModels.map((m) => ({
    key: m.key,
    display_name: m.display_name,
  }));

  const hasFeatureImportances =
    selectedModel?.metrics?.feature_importances &&
    selectedModel.metrics.feature_importances.length > 0;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
      {/* ── Section: Model Cards ──────────────────────────────────────────── */}
      <section>
        <div className="mb-4">
          <h2 className="text-white font-bold text-lg">ML Models</h2>
          <p className="text-slate-500 text-sm mt-0.5">
            Three models trained on pod failure data — click a card to inspect its details.
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {models.map((model) => (
            <ModelCard
              key={model.key}
              model={model}
              isSelected={selectedModel?.key === model.key}
              onClick={() => {
                setSelectedModel(model);
                setShowFeatureImportance(false);
              }}
            />
          ))}
        </div>
      </section>

      {/* ── Section: Metrics Comparison ───────────────────────────────────── */}
      {trainedModels.length >= 2 && (
        <section className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <p className="text-slate-500 text-xs font-mono uppercase tracking-wider mb-4">
            Performance Comparison
          </p>
          <MetricsComparisonChart models={models} />
        </section>
      )}

      {/* ── Section: Selected Model Detail ────────────────────────────────── */}
      {selectedModel && selectedModel.trained && selectedModel.metrics && (
        <section className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-5">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <span
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: MODEL_COLORS[selectedModel.key] ?? '#94a3b8' }}
              />
              <h3 className="text-white font-semibold">{selectedModel.display_name} — Detail</h3>
            </div>
            {hasFeatureImportances && (
              <button
                onClick={() => setShowFeatureImportance((v) => !v)}
                className="px-3 py-1.5 text-xs font-mono rounded-lg bg-slate-800 border border-slate-700 text-slate-400 hover:text-slate-200 hover:border-slate-500 transition-all"
              >
                {showFeatureImportance ? 'Hide' : 'Show'} Feature Importances
              </button>
            )}
          </div>

          {/* Metrics grid */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {(
              [
                ['Accuracy', 'accuracy'],
                ['Precision', 'precision'],
                ['Recall', 'recall'],
                ['F1 Score', 'f1'],
                ['ROC-AUC', 'roc_auc'],
              ] as [string, keyof ModelMetrics][]
            ).map(([label, key]) => {
              const val = selectedModel.metrics![key] as number | null | undefined;
              return (
                <div
                  key={key}
                  className="flex flex-col items-center gap-1 p-3 rounded-xl bg-slate-800/60 border border-slate-700/40"
                >
                  <span
                    className="text-xl font-mono font-bold"
                    style={{ color: MODEL_COLORS[selectedModel.key] ?? '#94a3b8' }}
                  >
                    {val != null ? `${(val * 100).toFixed(1)}%` : 'N/A'}
                  </span>
                  <span className="text-slate-500 text-[10px] font-mono uppercase tracking-wider">
                    {label}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Confusion matrix */}
          {selectedModel.metrics.confusion_matrix && (
            <div>
              <p className="text-slate-500 text-[10px] font-mono uppercase tracking-wider mb-2">
                Confusion Matrix (Healthy / Failure)
              </p>
              <div className="inline-grid grid-cols-2 gap-2">
                {selectedModel.metrics.confusion_matrix.flat().map((val, i) => {
                  const isCorrect = i === 0 || i === 3;
                  return (
                    <div
                      key={i}
                      className={`w-20 h-16 flex flex-col items-center justify-center rounded-xl border text-sm font-mono font-bold ${
                        isCorrect
                          ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                          : 'bg-red-500/10 border-red-500/30 text-red-400'
                      }`}
                    >
                      {val}
                      <span className="text-[9px] font-normal opacity-60 mt-0.5">
                        {i === 0 ? 'TN' : i === 1 ? 'FP' : i === 2 ? 'FN' : 'TP'}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Feature importances (expandable) */}
          {showFeatureImportance && hasFeatureImportances && (
            <div>
              <p className="text-slate-500 text-[10px] font-mono uppercase tracking-wider mb-3">
                Feature Importances
              </p>
              <FeatureImportanceChart
                importances={selectedModel.metrics!.feature_importances!}
                color={MODEL_COLORS[selectedModel.key] ?? '#94a3b8'}
              />
            </div>
          )}
        </section>
      )}

      {/* ── Section: Live Prediction Widget ───────────────────────────────── */}
      <section className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
        <div className="mb-5">
          <p className="text-slate-500 text-xs font-mono uppercase tracking-wider mb-1">
            Live Prediction
          </p>
          <h3 className="text-white font-semibold">Pod Failure Detection</h3>
          <p className="text-slate-500 text-sm mt-0.5">
            Enter pod metrics to predict failure risk using a trained model.
          </p>
        </div>
        <PredictionWidget availableModels={availableForPrediction} />
      </section>
    </div>
  );
}
