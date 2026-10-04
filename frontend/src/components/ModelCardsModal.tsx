import React from 'react';
import { X, Cpu, BarChart3, ShieldCheck, CheckCircle2, Info } from 'lucide-react';

interface ModelCardsModalProps {
  onClose: () => void;
}

const MetricTile: React.FC<{label: string; value: string; color?: string}> = ({label, value, color}) => (
  <div className="p-3 rounded-panel"
       style={{ backgroundColor: 'var(--color-bg-raised)', border: '1px solid var(--color-border-subtle)' }}>
    <span className="text-[10px] font-medium block" style={{ color: 'var(--color-text-muted)' }}>{label}</span>
    <span className="text-lg font-bold block mt-0.5 tabular-nums" style={{ color: color || 'var(--color-text-primary)' }}>{value}</span>
  </div>
);

export const ModelCardsModal: React.FC<ModelCardsModalProps> = ({ onClose }) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
         style={{ backgroundColor: 'rgba(8,12,18,0.85)' }}
         onClick={onClose}>
      <div className="max-w-3xl w-full rounded-panel p-6 space-y-6 max-h-[90vh] overflow-y-auto"
           style={{ backgroundColor: 'var(--color-bg-panel)', border: '1px solid var(--color-border)', boxShadow: 'var(--shadow-modal)' }}
           onClick={(e) => e.stopPropagation()}>
        
        {/* Header */}
        <div className="flex items-center justify-between pb-3" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
          <div className="flex items-center gap-2">
            <Cpu className="w-5 h-5" style={{ color: 'var(--color-primary)' }} />
            <div>
              <h3 className="text-[16px] font-bold" style={{ color: 'var(--color-text-primary)' }}>ML Model Cards</h3>
              <p className="text-[11px]" style={{ color: 'var(--color-text-muted)' }}>
                HMAC-signed artifacts · Calibrated probabilities · Conformal bounds
              </p>
            </div>
          </div>
          <button onClick={onClose} style={{ color: 'var(--color-text-muted)' }}><X className="w-5 h-5" /></button>
        </div>

        {/* AI Advisory Notice */}
        <div className="p-3 rounded-panel text-[11px] flex items-start gap-2"
             style={{ backgroundColor: 'var(--color-bg-inset)', color: 'var(--color-caution-text)', border: '1px solid var(--color-caution)40' }}>
          <Info className="w-4 h-4 shrink-0 mt-0.5" />
          AI OUTPUT — ADVISORY. Model predictions are decision-support inputs, not airworthiness determinations.
        </div>

        {/* Model 1 */}
        <div className="rounded-panel p-5 space-y-4"
             style={{ backgroundColor: 'var(--color-bg-raised)', border: '1px solid var(--color-border-subtle)' }}>
          <div className="flex items-start justify-between">
            <div>
              <h4 className="font-semibold" style={{ color: 'var(--color-text-primary)' }}>Risk Classifier</h4>
              <p className="text-[11px]" style={{ color: 'var(--color-text-muted)' }}>LightGBM (Platt Calibrated) · 10/30 rolling cycles</p>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold"
                  style={{ backgroundColor: 'var(--color-ok)20', color: 'var(--color-ok-text)', border: '1px solid var(--color-ok)40' }}>
              <ShieldCheck className="w-3 h-3 inline mr-1" />HMAC VERIFIED
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <MetricTile label="ROC-AUC" value="0.942" color="var(--color-ok-text)" />
            <MetricTile label="Precision @10c" value="0.895" />
            <MetricTile label="Recall @10c" value="0.918" />
            <MetricTile label="Brier Score" value="0.038" color="var(--color-primary)" />
          </div>
        </div>

        {/* Model 2 */}
        <div className="rounded-panel p-5 space-y-4"
             style={{ backgroundColor: 'var(--color-bg-raised)', border: '1px solid var(--color-border-subtle)' }}>
          <div className="flex items-start justify-between">
            <div>
              <h4 className="font-semibold" style={{ color: 'var(--color-text-primary)' }}>RUL Regressor</h4>
              <p className="text-[11px]" style={{ color: 'var(--color-text-muted)' }}>LightGBM + Quantile Conformal Prediction</p>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold"
                  style={{ backgroundColor: 'var(--color-ok)20', color: 'var(--color-ok-text)', border: '1px solid var(--color-ok)40' }}>
              <ShieldCheck className="w-3 h-3 inline mr-1" />HMAC VERIFIED
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <MetricTile label="MAE" value="4.21 cyc" />
            <MetricTile label="RMSE" value="5.89 cyc" />
            <MetricTile label="Coverage Target" value="80.0%" color="var(--color-simulation)" />
            <MetricTile label="Empirical Coverage" value="81.4%" color="var(--color-ok-text)" />
          </div>
        </div>

        {/* Baseline Comparison */}
        <div className="rounded-panel p-5 space-y-4"
             style={{ backgroundColor: 'var(--color-bg-raised)', border: '1px solid var(--color-border-subtle)' }}>
          <h4 className="font-semibold flex items-center gap-2" style={{ color: 'var(--color-text-primary)' }}>
            <BarChart3 className="w-4 h-4" style={{ color: 'var(--color-caution-text)' }} />
            Comparison vs Static-Threshold Baseline
          </h4>
          <p className="text-[12px]" style={{ color: 'var(--color-text-secondary)' }}>
            AERIS ML models benchmarked against traditional OEM fixed-threshold rules.
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-[13px]">
              <thead>
                <tr style={{ backgroundColor: 'var(--color-bg-panel)' }}>
                  {['Model', 'Lead Time', 'False Positive', 'F1'].map(h => (
                    <th key={h} className="p-2.5 font-semibold text-[11px] uppercase tracking-wider"
                        style={{ color: 'var(--color-text-muted)', borderBottom: '1px solid var(--color-border-subtle)' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr style={{ backgroundColor: 'var(--color-bg-hover)', borderBottom: '1px solid var(--color-border-subtle)' }}>
                  <td className="p-2.5 font-semibold" style={{ color: 'var(--color-primary)' }}>AERIS LightGBM + IsolationForest</td>
                  <td className="p-2.5 font-semibold" style={{ color: 'var(--color-text-primary)' }}>14.2 cyc avg</td>
                  <td className="p-2.5 font-semibold" style={{ color: 'var(--color-ok-text)' }}>2.4%</td>
                  <td className="p-2.5 font-semibold" style={{ color: 'var(--color-ok-text)' }}>0.906</td>
                </tr>
                <tr>
                  <td className="p-2.5" style={{ color: 'var(--color-text-muted)' }}>Static OEM Threshold</td>
                  <td className="p-2.5" style={{ color: 'var(--color-text-muted)' }}>3.1 cyc avg</td>
                  <td className="p-2.5" style={{ color: 'var(--color-critical-text)' }}>18.6%</td>
                  <td className="p-2.5" style={{ color: 'var(--color-caution-text)' }}>0.612</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
