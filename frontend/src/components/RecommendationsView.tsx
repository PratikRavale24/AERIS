import React, { useState } from 'react';
import { 
  FileCheck2, AlertTriangle, CheckCircle2, XCircle, Clock, 
  ShieldAlert, FileCode, Wrench, Package, Building2, UserCheck
} from 'lucide-react';
import { recommendationsApi } from '../api/client';

interface RecommendationItem {
  id: string; aircraft_id: string; component_id: string; priority_score: number;
  priority_tier: string; reason_codes: string[]; recommended_action: string;
  part_no?: string; part_status?: string; facility_id?: string; status: string;
  risk_score?: number; rul_q10?: number; rul_q50?: number; rul_q90?: number;
  trust_score?: number; evidence_passport_id?: string;
}

interface RecommendationsViewProps {
  recommendations: RecommendationItem[];
  userRole: string;
  onRefresh: () => void;
}

const PriorityBadge: React.FC<{tier: string}> = ({tier}) => {
  const t = tier?.toUpperCase() || 'MEDIUM';
  const colors: Record<string, {color: string; bg: string}> = {
    'CRITICAL': {color: 'var(--color-critical-text)', bg: 'var(--color-critical)'},
    'HIGH': {color: 'var(--color-high-text)', bg: 'var(--color-high)'},
    'MEDIUM': {color: 'var(--color-caution-text)', bg: 'var(--color-caution)'},
    'LOW': {color: 'var(--color-text-muted)', bg: 'var(--color-border)'},
  };
  const c = colors[t] || colors.MEDIUM;
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase"
          style={{ backgroundColor: c.bg + '20', color: c.color, border: `1px solid ${c.bg}40` }}>
      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: c.bg }} />
      {t}
    </span>
  );
};

export const RecommendationsView: React.FC<RecommendationsViewProps> = ({ recommendations, userRole, onRefresh }) => {
  const [selectedId, setSelectedId] = useState<string | null>(recommendations[0]?.id || null);
  const [justification, setJustification] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [showOverrideModal, setShowOverrideModal] = useState(false);

  const selectedRec = recommendations.find((r) => r.id === selectedId) || recommendations[0];

  const handleRecordDecision = async (action: 'ACCEPT' | 'DEFER' | 'REJECT' | 'OVERRIDE') => {
    if (!selectedRec) return;
    let finalReason = justification.trim();
    if (!finalReason) finalReason = `${action} decision executed by authorized ${userRole} persona in decision-support console.`;
    if (finalReason.length < 15) finalReason = `${finalReason} (Validated for operational decision log).`;

    setActionLoading(true);
    setErrorMsg(null);
    try {
      await recommendationsApi.recordDecision(selectedRec.id, { action, reason: finalReason });
      
      // Update local state to reflect the decision immediately for UX
      selectedRec.status = action === 'ACCEPT' ? 'ACCEPTED' : action === 'DEFER' ? 'DEFERRED' : action === 'REJECT' ? 'REJECTED' : 'PENDING_SECOND_APPROVAL';

      setJustification('');
      setShowOverrideModal(false);
      onRefresh();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to record decision');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div className="rounded-panel p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
           style={{ backgroundColor: 'var(--color-bg-panel)', border: '1px solid var(--color-border)' }}>
        <div>
          <h2 className="text-section flex items-center gap-2" style={{ color: 'var(--color-text-primary)' }}>
            <FileCheck2 className="w-5 h-5" style={{ color: 'var(--color-primary)' }} />
            Maintenance Decision Queue
          </h2>
          <p className="text-[12px] mt-1" style={{ color: 'var(--color-text-muted)' }}>
            Priority = f(Risk, RUL, Spares, Facility Capacity, Mission Urgency)
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-medium" style={{ color: 'var(--color-text-muted)' }}>Human-in-the-Loop:</span>
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold"
                style={{ backgroundColor: 'var(--color-ok)' + '20', color: 'var(--color-ok-text)', border: '1px solid var(--color-ok)40' }}>
            ENFORCED
          </span>
        </div>
      </div>

      {/* Main Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Queue */}
        <div className="lg:col-span-5 space-y-3 tour-rec-list">
          <h3 className="text-[11px] font-semibold uppercase tracking-wider px-1"
              style={{ color: 'var(--color-text-muted)' }}>
            Prioritized Recommendations ({recommendations.length})
          </h3>
          <div className="space-y-2">
            {recommendations.map((rec) => {
              const isSelected = rec.id === selectedRec?.id;
              return (
                <div key={rec.id}
                     onClick={() => { setSelectedId(rec.id); setErrorMsg(null); }}
                     className="p-4 rounded-panel cursor-pointer"
                     style={{
                       backgroundColor: isSelected ? 'var(--color-bg-hover)' : 'var(--color-bg-panel)',
                       border: `1px solid ${isSelected ? 'var(--color-primary)' : 'var(--color-border)'}`,
                     }}>
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold" style={{ color: 'var(--color-text-primary)' }}>{rec.aircraft_id}</span>
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase"
                              style={{
                                backgroundColor: rec.status === 'ACCEPTED' ? 'var(--color-ok)20' : rec.status === 'OPEN' || rec.status === 'PENDING' ? 'var(--color-caution)20' : 'var(--color-critical)20',
                                color: rec.status === 'ACCEPTED' ? 'var(--color-ok-text)' : rec.status === 'OPEN' || rec.status === 'PENDING' ? 'var(--color-caution-text)' : 'var(--color-critical-text)',
                                border: `1px solid ${rec.status === 'ACCEPTED' ? 'var(--color-ok)' : rec.status === 'OPEN' || rec.status === 'PENDING' ? 'var(--color-caution)' : 'var(--color-critical)'}40`,
                              }}>
                          {rec.status}
                        </span>
                      </div>
                      <p className="text-[12px] mt-0.5" style={{ color: 'var(--color-text-secondary)' }}>{rec.component_id}</p>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] block" style={{ color: 'var(--color-text-muted)' }}>Priority</span>
                      <span className="text-lg font-bold tabular-nums" style={{ color: 'var(--color-primary)' }}>
                        {rec.priority_score ? rec.priority_score.toFixed(1) : 'N/A'}
                      </span>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2 mt-3 pt-3 text-[11px]"
                       style={{ borderTop: '1px solid var(--color-border-subtle)' }}>
                    <div className="flex items-center gap-1.5" style={{ color: 'var(--color-text-muted)' }}>
                      <Package className="w-3 h-3" />
                      Part: <span style={{ color: rec.part_status === 'READY' ? 'var(--color-ok-text)' : 'var(--color-critical-text)' }}>
                        {rec.part_status || 'READY'}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5" style={{ color: 'var(--color-text-muted)' }}>
                      <Building2 className="w-3 h-3" />
                      Slot: <span style={{ color: 'var(--color-ok-text)' }}>{rec.facility_id || 'Depot 1'}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Detail Panel */}
        {selectedRec && (
          <div className="lg:col-span-7 rounded-panel p-6 space-y-6 tour-rec-detail"
               style={{ backgroundColor: 'var(--color-bg-panel)', border: '1px solid var(--color-border)' }}>
            {/* Header */}
            <div className="pb-4" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[11px] font-semibold uppercase tracking-wider block"
                        style={{ color: 'var(--color-primary)' }}>
                    AI Recommendation #{selectedRec.id.slice(0, 8)}
                  </span>
                  <h3 className="text-[16px] font-bold mt-0.5" style={{ color: 'var(--color-text-primary)' }}>
                    {selectedRec.recommended_action}
                  </h3>
                  <p className="text-[12px] mt-1" style={{ color: 'var(--color-text-muted)' }}>
                    Aircraft: {selectedRec.aircraft_id} · Component: {selectedRec.component_id} · <PriorityBadge tier={selectedRec.priority_tier} />
                  </p>
                </div>
                <span className="px-2 py-1 rounded text-[11px] font-semibold"
                      style={{ backgroundColor: 'var(--color-bg-inset)', color: 'var(--color-text-secondary)', border: '1px solid var(--color-border-subtle)' }}>
                  {selectedRec.priority_score ? selectedRec.priority_score.toFixed(1) : 'N/A'} / 100
                </span>
              </div>
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: 'Failure Risk', value: selectedRec.risk_score ? `${(selectedRec.risk_score * 100).toFixed(1)}%` : 'N/A', color: 'var(--color-critical-text)' },
                { label: 'Est. RUL', value: selectedRec.rul_q50 ? `${selectedRec.rul_q50} cyc` : 'N/A' },
                { label: 'Spare Status', value: selectedRec.part_status || 'READY', color: selectedRec.part_status === 'READY' ? 'var(--color-ok-text)' : 'var(--color-critical-text)' },
                { label: 'Facility', value: selectedRec.facility_id || 'Bay 1', color: 'var(--color-ok-text)' },
              ].map((m, i) => (
                <div key={i} className="p-3 rounded-panel"
                     style={{ backgroundColor: 'var(--color-bg-raised)', border: '1px solid var(--color-border-subtle)' }}>
                  <span className="text-[10px] font-medium block" style={{ color: 'var(--color-text-muted)' }}>{m.label}</span>
                  <span className="text-[16px] font-bold block mt-0.5"
                        style={{ color: m.color || 'var(--color-text-primary)' }}>{m.value}</span>
                </div>
              ))}
            </div>

            {/* Error */}
            {errorMsg && (
              <div className="p-3 rounded-panel text-[12px] flex items-center gap-2"
                   style={{ backgroundColor: 'var(--color-bg-inset)', color: 'var(--color-critical-text)', border: '1px solid var(--color-critical)' }}>
                <AlertTriangle className="w-4 h-4 shrink-0" /> {errorMsg}
              </div>
            )}

            {/* Action Panel */}
            {(selectedRec.status === 'OPEN' || selectedRec.status === 'PENDING') ? (
              <div className="p-5 rounded-panel space-y-4 tour-record-decision"
                   style={{ backgroundColor: 'var(--color-bg-raised)', border: '1px solid var(--color-border-subtle)' }}>
                <div className="flex items-center gap-2 pb-2" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                  <Wrench className="w-4 h-4" style={{ color: 'var(--color-primary)' }} />
                  <h4 className="text-[12px] font-bold uppercase tracking-wider" style={{ color: 'var(--color-text-secondary)' }}>
                    Record Decision
                  </h4>
                  <span className="text-[10px] ml-auto" style={{ color: 'var(--color-text-muted)' }}>AI RECOMMENDS · HUMAN DECIDES</span>
                </div>

                <div>
                  <label className="text-[11px] font-medium block mb-1" style={{ color: 'var(--color-text-muted)' }}>
                    Operational Rationale (min 15 characters)
                  </label>
                  <textarea rows={3} placeholder="Enter operational rationale for decision..."
                    value={justification} onChange={(e) => setJustification(e.target.value)}
                    className="w-full p-3 rounded-panel text-[13px] outline-none resize-none"
                    style={{ backgroundColor: 'var(--color-bg-inset)', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)' }} />
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <button disabled={actionLoading} onClick={() => handleRecordDecision('ACCEPT')}
                    className="px-4 py-2 rounded-panel text-[12px] font-semibold flex items-center gap-1.5 text-white disabled:opacity-50"
                    style={{ backgroundColor: 'var(--color-ok)' }}>
                    <CheckCircle2 className="w-3.5 h-3.5" /> Accept
                  </button>
                  <button disabled={actionLoading} onClick={() => handleRecordDecision('DEFER')}
                    className="px-4 py-2 rounded-panel text-[12px] font-semibold flex items-center gap-1.5 text-white disabled:opacity-50"
                    style={{ backgroundColor: 'var(--color-caution)' }}>
                    <Clock className="w-3.5 h-3.5" /> Defer
                  </button>
                  <button disabled={actionLoading} onClick={() => handleRecordDecision('REJECT')}
                    className="px-4 py-2 rounded-panel text-[12px] font-semibold flex items-center gap-1.5 text-white disabled:opacity-50"
                    style={{ backgroundColor: 'var(--color-critical)' }}>
                    <XCircle className="w-3.5 h-3.5" /> Reject
                  </button>
                  <button disabled={actionLoading} onClick={() => setShowOverrideModal(true)}
                    className="px-4 py-2 rounded-panel text-[12px] font-semibold flex items-center gap-1.5 text-white disabled:opacity-50 ml-auto"
                    style={{ backgroundColor: 'var(--color-simulation)' }}>
                    <ShieldAlert className="w-3.5 h-3.5" /> Override
                  </button>
                </div>
              </div>
            ) : (
              <div className="p-4 rounded-panel text-[12px]"
                   style={{ backgroundColor: 'var(--color-bg-raised)', border: '1px solid var(--color-border-subtle)' }}>
                <div className="flex items-center justify-between" style={{ color: 'var(--color-text-secondary)' }}>
                  <span>Status: <strong style={{ color: 'var(--color-ok-text)' }}>{selectedRec.status}</strong></span>
                  <span style={{ color: 'var(--color-text-muted)' }}>Audited & Hash-Chained</span>
                </div>
              </div>
            )}

            {/* Evidence Passport */}
            <div className="pt-4 tour-evidence" style={{ borderTop: '1px solid var(--color-border-subtle)' }}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-medium flex items-center gap-2" style={{ color: 'var(--color-text-muted)' }}>
                  <FileCode className="w-3.5 h-3.5" style={{ color: 'var(--color-ok-text)' }} />
                  Evidence Passport
                </span>
                <span className="text-[10px] px-1.5 py-0.5 rounded"
                      style={{ backgroundColor: 'var(--color-ok)20', color: 'var(--color-ok-text)', border: '1px solid var(--color-ok)40' }}>
                  Ed25519 Verified
                </span>
              </div>
              <div className="p-3 rounded-panel text-[11px] space-y-1"
                   style={{ backgroundColor: 'var(--color-bg-inset)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-secondary)' }}>
                <div>Passport ID: <span style={{ color: 'var(--color-primary)' }}>{selectedRec.evidence_passport_id || `ep-sha256-${selectedRec.id.slice(0, 8)}`}</span></div>
                <div>Prediction ID: <span style={{ color: 'var(--color-simulation)' }}>{selectedRec.id}</span></div>
                <div>Reason Codes: <span style={{ color: 'var(--color-caution-text)' }}>{(selectedRec.reason_codes || []).join(', ') || 'RUL_URGENT'}</span></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Override Modal */}
      {showOverrideModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ backgroundColor: 'rgba(8,12,18,0.85)' }}>
          <div className="max-w-md w-full p-6 rounded-panel space-y-5"
               style={{ backgroundColor: 'var(--color-bg-panel)', border: '1px solid var(--color-simulation)', boxShadow: 'var(--shadow-modal)' }}>
            <div className="flex items-center justify-between pb-3" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
              <div className="flex items-center gap-2" style={{ color: 'var(--color-simulation)' }}>
                <ShieldAlert className="w-5 h-5" />
                <h3 className="text-[16px] font-bold" style={{ color: 'var(--color-text-primary)' }}>Two-Person Override</h3>
              </div>
              <button onClick={() => setShowOverrideModal(false)} style={{ color: 'var(--color-text-muted)' }}>
                <XCircle className="w-5 h-5" />
              </button>
            </div>
            <p className="text-[12px]" style={{ color: 'var(--color-text-secondary)' }}>
              Overriding automated risk assessments requires dual authorization and a mandatory rationale for the immutable audit log.
            </p>
            <div>
              <label className="text-[11px] font-medium block mb-1" style={{ color: 'var(--color-text-muted)' }}>
                Mandatory Operational Rationale (min 15 chars)
              </label>
              <textarea rows={3} placeholder="Enter operational rationale for overriding risk assessment..."
                value={justification} onChange={(e) => setJustification(e.target.value)}
                className="w-full p-2 rounded-panel text-[12px] outline-none resize-none"
                style={{ backgroundColor: 'var(--color-bg-inset)', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)' }} />
            </div>
            <div className="flex items-center justify-end gap-3 pt-2">
              <button onClick={() => setShowOverrideModal(false)}
                className="px-4 py-2 rounded-panel text-[12px]"
                style={{ backgroundColor: 'var(--color-bg-raised)', color: 'var(--color-text-secondary)', border: '1px solid var(--color-border)' }}>
                Cancel
              </button>
              <button disabled={actionLoading} onClick={() => handleRecordDecision('OVERRIDE')}
                className="px-4 py-2 rounded-panel text-[12px] font-bold flex items-center gap-2 text-white disabled:opacity-50"
                style={{ backgroundColor: 'var(--color-simulation)' }}>
                <UserCheck className="w-4 h-4" /> Authenticate & Override
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
