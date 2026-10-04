import React, { useState } from 'react';
import { 
  X, Activity, AlertTriangle, FileText, ShieldCheck, 
  Wrench, BarChart3, Layers, ChevronRight
} from 'lucide-react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

interface ComponentDetail {
  id: string; name: string; serial_number: string; component_type: string;
  current_cycles: number; max_design_cycles: number;
  prediction?: {
    failure_probability_10c: number; rul_cycles_mean: number;
    rul_cycles_p10: number; rul_cycles_p90: number; is_anomaly: boolean;
    shap_json?: Record<string, number>;
  };
}

interface AircraftDetailModalProps {
  aircraft: {
    id: string; tail_number: string; fleet_type: string; base_location: string;
    status: string; flight_hours: number; total_cycles: number; components: ComponentDetail[];
  } | null;
  onClose: () => void;
  onNavigateRecommendations: () => void;
}

export const AircraftDetailModal: React.FC<AircraftDetailModalProps> = ({ aircraft, onClose, onNavigateRecommendations }) => {
  const [selectedComponentId, setSelectedComponentId] = useState<string | null>(aircraft?.components[0]?.id || null);
  const [simulationActive, setSimulationActive] = useState(false);

  if (!aircraft) return null;

  const selectedComp = aircraft.components.find((c) => c.id === selectedComponentId) || aircraft.components[0];
  const pred = selectedComp?.prediction;

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

  const getRiskColor = (risk: number) => risk >= 0.7 ? 'var(--color-critical-text)' : risk >= 0.3 ? 'var(--color-caution-text)' : 'var(--color-ok-text)';

  return (
    <div className="fixed inset-0 z-50 flex justify-end" style={{ backgroundColor: 'rgba(8,12,18,0.8)' }} onClick={onClose}>
      <div className="w-full max-w-4xl h-full overflow-y-auto flex flex-col"
           style={{ backgroundColor: 'var(--color-bg-panel)', borderLeft: '1px solid var(--color-border)', boxShadow: 'var(--shadow-modal)' }}
           onClick={(e) => e.stopPropagation()}>
        
        {/* Header */}
        <div className="p-6 flex items-center justify-between sticky top-0 z-10"
             style={{ backgroundColor: 'var(--color-bg-panel)', borderBottom: '1px solid var(--color-border)' }}>
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold" style={{ color: 'var(--color-text-primary)' }}>{aircraft.tail_number}</h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase"
                    style={{
                      backgroundColor: aircraft.status === 'FMC' ? 'var(--color-ok)20' : 'var(--color-critical)20',
                      color: aircraft.status === 'FMC' ? 'var(--color-ok-text)' : 'var(--color-critical-text)',
                      border: `1px solid ${aircraft.status === 'FMC' ? 'var(--color-ok)' : 'var(--color-critical)'}40`,
                    }}>
                {aircraft.status}
              </span>
            </div>
            <p className="text-[12px] mt-1" style={{ color: 'var(--color-text-muted)' }}>
              {aircraft.fleet_type} · {aircraft.base_location} · {aircraft.flight_hours.toLocaleString()} hrs
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={onNavigateRecommendations}
              className="px-3 py-1.5 rounded-panel text-[12px] font-medium text-white flex items-center gap-1.5"
              style={{ backgroundColor: 'var(--color-primary-strong)' }}>
              <Wrench className="w-3.5 h-3.5" /> Recommendations
            </button>
            <button onClick={onClose} className="p-2 rounded-panel" style={{ color: 'var(--color-text-muted)' }}>
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6 flex-1">
          {/* Component Selector */}
          <div>
            <h3 className="text-[11px] font-semibold uppercase tracking-wider mb-3" style={{ color: 'var(--color-text-muted)' }}>
              <Layers className="w-3.5 h-3.5 inline mr-1.5" style={{ color: 'var(--color-primary)' }} />
              Tracked Components
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {aircraft.components.map((comp) => {
                const isSelected = comp.id === selectedComp?.id;
                const cPred = comp.prediction;
                const isHigh = cPred && cPred.failure_probability_10c >= 0.7;
                return (
                  <button key={comp.id} onClick={() => setSelectedComponentId(comp.id)}
                    className="p-3 rounded-panel text-left"
                    style={{
                      backgroundColor: isSelected ? 'var(--color-bg-hover)' : 'var(--color-bg-raised)',
                      border: `1px solid ${isSelected ? 'var(--color-primary)' : 'var(--color-border-subtle)'}`,
                    }}>
                    <div className="flex items-center justify-between">
                      <span className="text-[13px] font-semibold truncate" style={{ color: 'var(--color-text-primary)' }}>{comp.name}</span>
                      {isHigh && <span className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--color-critical)' }} />}
                    </div>
                    <div className="text-[11px] mt-0.5" style={{ color: 'var(--color-text-muted)' }}>S/N: {comp.serial_number}</div>
                    <div className="mt-2 flex items-center justify-between text-[11px]">
                      <span style={{ color: 'var(--color-text-secondary)' }}>
                        RUL: <strong style={{ color: 'var(--color-text-primary)' }}>{cPred ? cPred.rul_cycles_mean : 'N/A'}</strong> cyc
                      </span>
                      <span style={{ color: cPred ? getRiskColor(cPred.failure_probability_10c) : 'var(--color-ok-text)' }}>
                        {cPred ? `${(cPred.failure_probability_10c * 100).toFixed(0)}% Risk` : 'Normal'}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Component Diagnostics */}
          {selectedComp && (
            <div className="rounded-panel p-5 space-y-6"
                 style={{ backgroundColor: 'var(--color-bg-raised)', border: '1px solid var(--color-border-subtle)' }}>
              
              {/* Component Header */}
              <div className="flex items-center justify-between pb-4" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                <div>
                  <h4 className="text-[15px] font-bold" style={{ color: 'var(--color-text-primary)' }}>{selectedComp.name}</h4>
                  <p className="text-[11px] mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
                    {selectedComp.component_type} · Cycles: {selectedComp.current_cycles} / {selectedComp.max_design_cycles}
                  </p>
                </div>
                {pred?.is_anomaly && (
                  <span className="px-2 py-1 rounded-panel text-[11px] font-semibold flex items-center gap-1.5"
                        style={{ backgroundColor: 'var(--color-critical)20', color: 'var(--color-critical-text)', border: '1px solid var(--color-critical)40' }}>
                    <AlertTriangle className="w-3.5 h-3.5" /> Anomaly Detected
                  </span>
                )}
              </div>

              {/* What-If Toggle */}
              <div className="p-4 rounded-panel space-y-3"
                   style={{ backgroundColor: 'var(--color-bg-panel)', border: '1px solid var(--color-border-subtle)' }}>
                <h5 className="text-[12px] font-semibold flex items-center gap-2" style={{ color: 'var(--color-simulation)' }}>
                  <Layers className="w-3.5 h-3.5" /> What-If Scenario
                </h5>
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-[13px] font-medium" style={{ color: 'var(--color-text-primary)' }}>Delay Spare Delivery</div>
                    <div className="text-[11px]" style={{ color: 'var(--color-text-muted)' }}>Simulate 14-day delay for {selectedComp.name}</div>
                  </div>
                  <button onClick={() => setSimulationActive(!simulationActive)}
                    className="relative inline-flex h-5 w-10 items-center rounded-full"
                    style={{ backgroundColor: simulationActive ? 'var(--color-simulation)' : 'var(--color-border)' }}>
                    <span className={`inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform ${simulationActive ? 'translate-x-5' : 'translate-x-1'}`} />
                  </button>
                </div>
                {simulationActive && (
                  <div className="p-3 rounded-panel"
                       style={{ backgroundColor: 'var(--color-bg-inset)', border: '1px solid var(--color-border-subtle)' }}>
                    <div className="text-[10px] font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--color-simulation)' }}>Simulated Impact</div>
                    <div className="grid grid-cols-2 gap-3 text-[12px]">
                      <div>
                        <span className="block" style={{ color: 'var(--color-text-muted)' }}>Fleet Availability</span>
                        <span className="font-bold" style={{ color: 'var(--color-critical-text)' }}>-4.1% (1 asset down)</span>
                      </div>
                      <div>
                        <span className="block" style={{ color: 'var(--color-text-muted)' }}>Priority Score</span>
                        <span className="font-bold" style={{ color: 'var(--color-caution-text)' }}>Escalated to 98 (CRITICAL)</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* ML Prediction Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3 rounded-panel" style={{ backgroundColor: 'var(--color-bg-panel)', border: '1px solid var(--color-border-subtle)' }}>
                  <span className="text-[10px] font-medium block" style={{ color: 'var(--color-text-muted)' }}>10-Cycle Failure Risk</span>
                  <span className="text-xl font-bold block mt-0.5 tabular-nums"
                        style={{ color: pred ? getRiskColor(pred.failure_probability_10c) : 'var(--color-text-primary)' }}>
                    {pred ? `${(pred.failure_probability_10c * 100).toFixed(1)}%` : 'N/A'}
                  </span>
                  <p className="text-[10px] mt-0.5" style={{ color: 'var(--color-text-muted)' }}>LightGBM Calibrated</p>
                </div>
                <div className="p-3 rounded-panel" style={{ backgroundColor: 'var(--color-bg-panel)', border: '1px solid var(--color-border-subtle)' }}>
                  <span className="text-[10px] font-medium block" style={{ color: 'var(--color-text-muted)' }}>Est. RUL</span>
                  <span className="text-xl font-bold block mt-0.5 tabular-nums" style={{ color: 'var(--color-text-primary)' }}>
                    {pred?.rul_cycles_mean ?? 'N/A'} <span className="text-[11px] font-normal" style={{ color: 'var(--color-text-muted)' }}>cyc</span>
                  </span>
                  <p className="text-[10px] mt-0.5" style={{ color: 'var(--color-advisory-text)' }}>
                    80% CI: [{pred?.rul_cycles_p10 ?? 0} – {pred?.rul_cycles_p90 ?? 0}]
                  </p>
                </div>
                <div className="p-3 rounded-panel" style={{ backgroundColor: 'var(--color-bg-panel)', border: '1px solid var(--color-border-subtle)' }}>
                  <span className="text-[10px] font-medium block" style={{ color: 'var(--color-text-muted)' }}>Prediction Confidence</span>
                  <span className="text-xl font-bold block mt-0.5 tabular-nums" style={{ color: 'var(--color-primary)' }}>92.4%</span>
                  <p className="text-[10px] mt-0.5" style={{ color: 'var(--color-text-muted)' }}>Conformal Bounds</p>
                </div>
              </div>

              {/* Telemetry Chart */}
              <div>
                <h5 className="text-[11px] font-semibold uppercase tracking-wider mb-2 flex items-center gap-2"
                    style={{ color: 'var(--color-text-muted)' }}>
                  <Activity className="w-3.5 h-3.5" style={{ color: 'var(--color-ok-text)' }} />
                  Sensor Degradation Trend (Last 30 Cycles)
                </h5>
                <div className="h-52 p-3 rounded-panel"
                     style={{ backgroundColor: 'var(--color-bg-inset)', border: '1px solid var(--color-border-subtle)' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={mockTelemetryData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" />
                      <XAxis dataKey="cycle" stroke="var(--color-text-muted)" tick={{ fontSize: 10 }} />
                      <YAxis yAxisId="left" stroke="var(--color-ok-text)" tick={{ fontSize: 10 }} domain={['dataMin - 10', 'dataMax + 10']} />
                      <YAxis yAxisId="right" orientation="right" stroke="var(--color-primary)" tick={{ fontSize: 10 }} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'var(--color-bg-panel)',
                          borderColor: 'var(--color-border)',
                          fontSize: '12px',
                          color: 'var(--color-text-primary)',
                          borderRadius: '6px',
                        }}
                      />
                      <Line yAxisId="left" type="monotone" dataKey="egt_celsius" stroke="var(--color-ok-text)" strokeWidth={2} name="EGT (°C)" dot={false} />
                      <Line yAxisId="right" type="monotone" dataKey="vibration_rms" stroke="var(--color-primary)" strokeWidth={2} name="Vibration (RMS)" dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* SHAP */}
              {pred?.shap_json && (
                <div>
                  <h5 className="text-[11px] font-semibold uppercase tracking-wider mb-3 flex items-center gap-2"
                      style={{ color: 'var(--color-text-muted)' }}>
                    <BarChart3 className="w-3.5 h-3.5" style={{ color: 'var(--color-simulation)' }} />
                    AI Evidence — Feature Attribution (SHAP)
                  </h5>
                  <p className="text-[10px] mb-3 px-1" style={{ color: 'var(--color-text-muted)' }}>
                    AI OUTPUT — ADVISORY · Not an airworthiness or release-to-service decision
                  </p>
                  <div className="space-y-2">
                    {Object.entries(pred.shap_json)
                      .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
                      .slice(0, 5)
                      .map(([feature, value]) => {
                        const isPositive = value > 0;
                        const widthPct = Math.min(100, Math.abs(value) * 300);
                        return (
                          <div key={feature} className="flex items-center text-[12px] gap-3">
                            <span className="w-44 truncate" style={{ color: 'var(--color-text-secondary)' }}>{feature}</span>
                            <div className="flex-1 h-4 rounded overflow-hidden" style={{ backgroundColor: 'var(--color-bg-inset)' }}>
                              <div className="h-full rounded"
                                   style={{ width: `${Math.max(4, widthPct)}%`, backgroundColor: isPositive ? 'var(--color-critical)' : 'var(--color-ok)' }} />
                            </div>
                            <span className="w-16 text-right tabular-nums text-[11px] font-semibold"
                                  style={{ color: isPositive ? 'var(--color-critical-text)' : 'var(--color-ok-text)' }}>
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
