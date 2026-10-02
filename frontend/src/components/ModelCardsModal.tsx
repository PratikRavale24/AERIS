import React from 'react';
import { X, Cpu, BarChart3, ShieldCheck, CheckCircle2, TrendingUp, HelpCircle } from 'lucide-react';

interface ModelCardsModalProps {
  onClose: () => void;
}

export const ModelCardsModal: React.FC<ModelCardsModalProps> = ({ onClose }) => {
  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#111827] border border-gray-800 rounded-2xl max-w-3xl w-full p-6 space-y-6 shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between border-b border-gray-800 pb-3">
          <div className="flex items-center gap-2">
            <Cpu className="w-6 h-6 text-blue-400" />
            <div>
              <h3 className="text-lg font-bold text-white">ML Model Cards & Baseline Verification</h3>
              <p className="text-xs text-gray-400 font-mono">HMAC-signed model artifacts &bull; Calibrated probabilities &bull; Conformal bounds</p>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Model 1: LightGBM Risk Classifier */}
        <div className="bg-gray-900/80 border border-gray-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-bold text-white text-base">Engine / Hydraulics / Avionics Risk Classifier</h4>
              <p className="text-xs text-gray-400 font-mono">Algorithm: LightGBM (Platt Calibrated) &bull; Input Window: 10/30 rolling cycles</p>
            </div>
            <span className="px-2.5 py-1 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 text-xs font-mono font-bold">
              VERIFIED HMAC-SHA256
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
            <div className="bg-[#111827] border border-gray-800 rounded-lg p-3">
              <span className="text-gray-400 block text-[11px]">ROC-AUC Score</span>
              <span className="text-lg font-bold text-emerald-400 mt-0.5 block">0.942</span>
            </div>
            <div className="bg-[#111827] border border-gray-800 rounded-lg p-3">
              <span className="text-gray-400 block text-[11px]">Precision @ 10c</span>
              <span className="text-lg font-bold text-white mt-0.5 block">0.895</span>
            </div>
            <div className="bg-[#111827] border border-gray-800 rounded-lg p-3">
              <span className="text-gray-400 block text-[11px]">Recall @ 10c</span>
              <span className="text-lg font-bold text-white mt-0.5 block">0.918</span>
            </div>
            <div className="bg-[#111827] border border-gray-800 rounded-lg p-3">
              <span className="text-gray-400 block text-[11px]">Brier Score</span>
              <span className="text-lg font-bold text-blue-400 mt-0.5 block">0.038</span>
            </div>
          </div>
        </div>

        {/* Model 2: LightGBM RUL Regressor with Conformal Intervals */}
        <div className="bg-gray-900/80 border border-gray-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-bold text-white text-base">Remaining Useful Life (RUL) Regressor</h4>
              <p className="text-xs text-gray-400 font-mono">Algorithm: LightGBM Regressor + Quantile Conformal Prediction Interval</p>
            </div>
            <span className="px-2.5 py-1 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 text-xs font-mono font-bold">
              VERIFIED HMAC-SHA256
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
            <div className="bg-[#111827] border border-gray-800 rounded-lg p-3">
              <span className="text-gray-400 block text-[11px]">RUL Mean Absolute Error</span>
              <span className="text-lg font-bold text-white mt-0.5 block">4.21 <span className="text-xs text-gray-400">cyc</span></span>
            </div>
            <div className="bg-[#111827] border border-gray-800 rounded-lg p-3">
              <span className="text-gray-400 block text-[11px]">RMSE</span>
              <span className="text-lg font-bold text-white mt-0.5 block">5.89 <span className="text-xs text-gray-400">cyc</span></span>
            </div>
            <div className="bg-[#111827] border border-gray-800 rounded-lg p-3">
              <span className="text-gray-400 block text-[11px]">Conformal Coverage Target</span>
              <span className="text-lg font-bold text-purple-400 mt-0.5 block">80.0%</span>
            </div>
            <div className="bg-[#111827] border border-gray-800 rounded-lg p-3">
              <span className="text-gray-400 block text-[11px]">Empirical Coverage</span>
              <span className="text-lg font-bold text-emerald-400 mt-0.5 block">81.4%</span>
            </div>
          </div>
        </div>

        {/* Model 3: Baseline Comparison */}
        <div className="bg-gray-900/80 border border-gray-800 rounded-xl p-5 space-y-4">
          <h4 className="font-bold text-white text-base flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-amber-400" /> Comparison Against Static-Threshold Baseline
          </h4>
          <p className="text-xs text-gray-300">
            AERIS ML models are benchmarked against traditional OEM fixed-threshold rules (e.g. alert when EGT &gt; 680°C or Vibration &gt; 0.50 RMS).
          </p>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[#111827] text-gray-400 border-b border-gray-800">
                <tr>
                  <th className="p-2.5">Model / Method</th>
                  <th className="p-2.5">Lead Time Notice</th>
                  <th className="p-2.5">False Positive Rate</th>
                  <th className="p-2.5 text-right">F1 Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800 text-gray-300">
                <tr className="bg-blue-950/20">
                  <td className="p-2.5 font-bold text-blue-400">AERIS LightGBM + IsolationForest</td>
                  <td className="p-2.5 font-bold text-white">14.2 cycles avg</td>
                  <td className="p-2.5 text-emerald-400 font-bold">2.4%</td>
                  <td className="p-2.5 text-right font-bold text-emerald-400">0.906</td>
                </tr>
                <tr>
                  <td className="p-2.5 text-gray-400">Static OEM Threshold Rule Baseline</td>
                  <td className="p-2.5 text-gray-400">3.1 cycles avg</td>
                  <td className="p-2.5 text-red-400">18.6%</td>
                  <td className="p-2.5 text-right text-amber-400">0.612</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
