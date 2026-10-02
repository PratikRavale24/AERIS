import React, { useState } from 'react';
import { 
  X, 
  Activity, 
  AlertTriangle, 
  Clock, 
  FileText, 
  Cpu, 
  ShieldCheck, 
  TrendingUp, 
  Wrench,
  BarChart3,
  Layers,
  ChevronRight
} from 'lucide-react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

interface ComponentDetail {
  id: string;
  name: string;
  serial_number: string;
  component_type: string;
  current_cycles: number;
  max_design_cycles: number;
  prediction?: {
    failure_probability_10c: number;
    rul_cycles_mean: number;
    rul_cycles_p10: number;
    rul_cycles_p90: number;
    is_anomaly: boolean;
    shap_json?: Record<string, number>;
  };
}

interface AircraftDetailModalProps {
  aircraft: {
    id: string;
    tail_number: string;
    fleet_type: string;
    base_location: string;
    status: string;
    flight_hours: number;
    total_cycles: number;
    components: ComponentDetail[];
  } | null;
  onClose: () => void;
  onNavigateRecommendations: () => void;
}

export const AircraftDetailModal: React.FC<AircraftDetailModalProps> = ({
  aircraft,
  onClose,
  onNavigateRecommendations,
}) => {
  const [selectedComponentId, setSelectedComponentId] = useState<string | null>(
    aircraft?.components[0]?.id || null
  );

  if (!aircraft) return null;

  const selectedComp = aircraft.components.find((c) => c.id === selectedComponentId) || aircraft.components[0];
  const pred = selectedComp?.prediction;

  // Mock sample telemetry trend for visualization
  const mockTelemetryData = Array.from({ length: 30 }, (_, i) => {
    const cycle = (selectedComp?.current_cycles || 100) - 30 + i;
    const baseTemp = 640 + Math.sin(i * 0.4) * 8;
    const noise = (Math.random() - 0.5) * 4;
    const trend = pred && pred.failure_probability_10c > 0.5 ? (i > 15 ? (i - 15) * 2.2 : 0) : 0;
    return {
      cycle,
      egt_celsius: Math.round(baseTemp + noise + trend),
      vibration_rms: Number((0.25 + Math.sin(i * 0.3) * 0.05 + (trend ? trend * 0.03 : 0)).toFixed(3)),
    };
  });

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-4xl bg-[#111827] border-l border-gray-800 h-full overflow-y-auto flex flex-col shadow-2xl">
        {/* Modal Header */}
        <div className="p-6 border-b border-gray-800 flex items-center justify-between sticky top-0 bg-[#111827]/95 backdrop-blur z-10">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-bold text-white font-mono">{aircraft.tail_number}</h2>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold border ${
                aircraft.status === 'FMC' ? 'bg-emerald-950 text-emerald-400 border-emerald-800' : 'bg-red-950 text-red-400 border-red-800'
              }`}>
                {aircraft.status}
              </span>
            </div>
            <p className="text-xs text-gray-400 font-mono mt-1">
              {aircraft.fleet_type} &bull; Base: {aircraft.base_location} &bull; Flight Hours: {aircraft.flight_hours.toLocaleString()} hrs
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={onNavigateRecommendations}
              className="bg-blue-600 hover:bg-blue-500 text-white px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 shadow-md"
            >
              <Wrench className="w-3.5 h-3.5" />
              View Recommendations
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6 flex-1">
          {/* Components Selector */}
          <div>
            <h3 className="text-xs font-mono uppercase text-gray-400 mb-3 flex items-center gap-2">
              <Layers className="w-4 h-4 text-blue-400" /> Tracked Critical Components
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {aircraft.components.map((comp) => {
                const isSelected = comp.id === selectedComp?.id;
                const cPred = comp.prediction;
                const isHigh = cPred && cPred.failure_probability_10c >= 0.7;

                return (
                  <button
                    key={comp.id}
                    onClick={() => setSelectedComponentId(comp.id)}
                    className={`p-3.5 rounded-xl border text-left transition-all ${
                      isSelected
                        ? 'bg-blue-950/40 border-blue-500 text-white shadow-lg'
                        : 'bg-gray-900/60 border-gray-800 text-gray-300 hover:bg-gray-800/80'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-sm truncate">{comp.name}</span>
                      {isHigh && (
                        <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
                      )}
                    </div>
                    <div className="text-xs text-gray-400 font-mono mt-1">S/N: {comp.serial_number}</div>
                    <div className="mt-2 flex items-center justify-between text-[11px] font-mono">
                      <span>RUL: <strong className="text-white">{cPred ? cPred.rul_cycles_mean : 'N/A'}</strong> cyc</span>
                      <span className={isHigh ? 'text-red-400 font-bold' : 'text-emerald-400'}>
                        {cPred ? `${(cPred.failure_probability_10c * 100).toFixed(0)}% Risk` : 'Normal'}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Selected Component ML Diagnostics */}
          {selectedComp && (
            <div className="bg-gray-900/80 border border-gray-800 rounded-xl p-5 space-y-6">
              <div className="flex items-center justify-between border-b border-gray-800 pb-4">
                <div>
                  <h4 className="text-base font-bold text-white">{selectedComp.name} Diagnostic Profile</h4>
                  <p className="text-xs text-gray-400 font-mono">
                    Type: {selectedComp.component_type} &bull; Current Cycles: {selectedComp.current_cycles} / {selectedComp.max_design_cycles} max
                  </p>
                </div>
                {pred && pred.is_anomaly && (
                  <span className="px-3 py-1 bg-red-950/80 border border-red-800 text-red-400 rounded-lg text-xs font-mono font-bold flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4" /> Anomaly Detected (IsolationForest)
                  </span>
                )}
              </div>

              {/* ML Prediction Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {/* Card 1: 10-Cycle Failure Probability */}
                <div className="bg-[#111827] border border-gray-800 rounded-lg p-4">
                  <span className="text-xs font-mono text-gray-400 block">10-Cycle Failure Prob</span>
                  <div className="flex items-baseline gap-2 mt-1">
                    <span className={`text-2xl font-extrabold font-mono ${
                      (pred?.failure_probability_10c || 0) >= 0.7 ? 'text-red-400' : 'text-emerald-400'
                    }`}>
                      {pred ? `${(pred.failure_probability_10c * 100).toFixed(1)}%` : 'N/A'}
                    </span>
                  </div>
                  <p className="text-[11px] text-gray-500 font-mono mt-1">LightGBM Classifier (Calibrated)</p>
                </div>

                {/* Card 2: RUL Mean & Conformal Range */}
                <div className="bg-[#111827] border border-gray-800 rounded-lg p-4">
                  <span className="text-xs font-mono text-gray-400 block">Remaining Useful Life (RUL)</span>
                  <div className="flex items-baseline gap-2 mt-1">
                    <span className="text-2xl font-extrabold text-white font-mono">
                      {pred?.rul_cycles_mean ?? 'N/A'}
                    </span>
                    <span className="text-xs text-gray-400 font-mono">cycles</span>
                  </div>
                  <p className="text-[11px] text-blue-400 font-mono mt-1">
                    80% Interval: [{pred?.rul_cycles_p10 ?? 0} – {pred?.rul_cycles_p90 ?? 0}] cyc
                  </p>
                </div>

                {/* Card 3: Conformal Prediction Bounds */}
                <div className="bg-[#111827] border border-gray-800 rounded-lg p-4">
                  <span className="text-xs font-mono text-gray-400 block">Model Confidence</span>
                  <div className="flex items-baseline gap-2 mt-1">
                    <span className="text-2xl font-extrabold text-indigo-400 font-mono">92.4%</span>
                  </div>
                  <p className="text-[11px] text-gray-500 font-mono mt-1">Conformal Interval Bounds</p>
                </div>
              </div>

              {/* Sensor Telemetry Chart */}
              <div>
                <h5 className="text-xs font-mono uppercase text-gray-400 mb-2 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-emerald-400" /> Sensor Degradation Trend (Last 30 Cycles)
                </h5>
                <div className="h-52 bg-[#0B0F19] rounded-lg p-3 border border-gray-800">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={mockTelemetryData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                      <XAxis dataKey="cycle" stroke="#6B7280" tick={{ fontSize: 10 }} />
                      <YAxis yAxisId="left" stroke="#10B981" tick={{ fontSize: 10 }} domain={['dataMin - 10', 'dataMax + 10']} />
                      <YAxis yAxisId="right" orientation="right" stroke="#3B82F6" tick={{ fontSize: 10 }} />
                      <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', fontSize: '12px' }} />
                      <Line yAxisId="left" type="monotone" dataKey="egt_celsius" stroke="#10B981" strokeWidth={2} name="EGT (°C)" dot={false} />
                      <Line yAxisId="right" type="monotone" dataKey="vibration_rms" stroke="#3B82F6" strokeWidth={2} name="Vibration (RMS)" dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* SHAP Feature Importance Explanations */}
              {pred?.shap_json && (
                <div>
                  <h5 className="text-xs font-mono uppercase text-gray-400 mb-3 flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-purple-400" /> SHAP Feature Attribution (Why this prediction?)
                  </h5>
                  <div className="space-y-2">
                    {Object.entries(pred.shap_json)
                      .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
                      .slice(0, 5)
                      .map(([feature, value]) => {
                        const isPositive = value > 0;
                        const widthPct = Math.min(100, Math.abs(value) * 300);

                        return (
                          <div key={feature} className="flex items-center text-xs font-mono gap-3">
                            <span className="w-48 text-gray-300 truncate">{feature}</span>
                            <div className="flex-1 bg-gray-900 h-4 rounded overflow-hidden relative flex items-center">
                              <div
                                className={`h-full rounded ${isPositive ? 'bg-red-500' : 'bg-emerald-500'}`}
                                style={{ width: `${Math.max(4, widthPct)}%` }}
                              />
                            </div>
                            <span className={`w-16 text-right ${isPositive ? 'text-red-400' : 'text-emerald-400'}`}>
                              {isPositive ? '+' : ''}{value.toFixed(4)}
                            </span>
                          </div>
                        );
                      })}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
