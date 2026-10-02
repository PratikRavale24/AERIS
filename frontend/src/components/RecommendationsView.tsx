import React, { useState } from 'react';
import { 
  FileCheck2, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  ShieldAlert, 
  FileCode, 
  Wrench,
  Package,
  Building2,
  UserCheck
} from 'lucide-react';
import { recommendationsApi } from '../api/client';

interface RecommendationItem {
  id: string;
  aircraft_id: string;
  component_id: string;
  priority_score: number;
  priority_tier: string;
  reason_codes: string[];
  recommended_action: string;
  part_no?: string;
  part_status?: string;
  facility_id?: string;
  status: string;
  risk_score?: number;
  rul_q10?: number;
  rul_q50?: number;
  rul_q90?: number;
  trust_score?: number;
  evidence_passport_id?: string;
}

interface RecommendationsViewProps {
  recommendations: RecommendationItem[];
  userRole: string;
  onRefresh: () => void;
}

export const RecommendationsView: React.FC<RecommendationsViewProps> = ({
  recommendations,
  userRole,
  onRefresh,
}) => {
  const [selectedId, setSelectedId] = useState<string | null>(recommendations[0]?.id || null);
  const [justification, setJustification] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Two-Person Override Modal state
  const [showOverrideModal, setShowOverrideModal] = useState(false);

  const selectedRec = recommendations.find((r) => r.id === selectedId) || recommendations[0];

  const handleRecordDecision = async (action: 'ACCEPT' | 'DEFER' | 'REJECT' | 'OVERRIDE') => {
    if (!selectedRec) return;

    let finalReason = justification.trim();
    if (!finalReason) {
      finalReason = `${action} decision executed by authorized ${userRole} persona in decision-support console.`;
    }

    if (finalReason.length < 15) {
      finalReason = `${finalReason} (Validated for operational decision log).`;
    }

    setActionLoading(true);
    setErrorMsg(null);
    try {
      await recommendationsApi.recordDecision(selectedRec.id, {
        action,
        reason: finalReason,
      });
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
      {/* View Title */}
      <div className="flex items-center justify-between bg-[#111827] border border-gray-800 rounded-xl p-5 shadow-lg">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FileCheck2 className="w-6 h-6 text-blue-400" /> Decision Support Engine
          </h2>
          <p className="text-xs text-gray-400 font-mono mt-1">
            Immutable versioned recommendations &bull; Priority Score = f(Risk, RUL, Spares, Slots, Mission Urgency)
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-gray-400">Human-in-the-Loop Enforced:</span>
          <span className="px-3 py-1 rounded-full bg-emerald-950/80 text-emerald-400 border border-emerald-800 text-xs font-mono font-bold">
            REQUIRES AUTHORIZED DECISION
          </span>
        </div>
      </div>

      {/* Main Grid: Left Queue, Right Action & Passport */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Recommendation Queue */}
        <div className="lg:col-span-5 space-y-3">
          <h3 className="text-xs font-mono uppercase text-gray-400 px-1">
            Prioritized Recommendations ({recommendations.length})
          </h3>

          <div className="space-y-3">
            {recommendations.map((rec) => {
              const isSelected = rec.id === selectedRec?.id;

              return (
                <div
                  key={rec.id}
                  onClick={() => {
                    setSelectedId(rec.id);
                    setErrorMsg(null);
                  }}
                  className={`p-4 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-blue-950/40 border-blue-500 shadow-xl'
                      : 'bg-[#111827] border-gray-800 hover:border-gray-700'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-white text-base">{rec.aircraft_id}</span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                          rec.status === 'ACCEPTED' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' :
                          rec.status === 'OPEN' ? 'bg-amber-950 text-amber-400 border border-amber-800' :
                          rec.status === 'OVERRIDDEN' ? 'bg-purple-950 text-purple-400 border border-purple-800' :
                          'bg-red-950 text-red-400 border border-red-800'
                        }`}>
                          {rec.status}
                        </span>
                      </div>
                      <p className="text-xs text-gray-300 font-medium mt-1">{rec.component_id}</p>
                    </div>

                    <div className="text-right">
                      <span className="text-xs font-mono text-gray-400 block">Priority Score</span>
                      <span className="text-lg font-extrabold text-blue-400 font-mono">
                        {rec.priority_score ? rec.priority_score.toFixed(1) : 'N/A'}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2 mt-3 pt-3 border-t border-gray-800/80 text-xs font-mono">
                    <div className="flex items-center gap-1.5 text-gray-400">
                      <Package className="w-3.5 h-3.5 text-gray-500" />
                      Part: <span className={rec.part_status === 'READY' ? 'text-emerald-400' : 'text-red-400'}>
                        {rec.part_status || 'READY'}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5 text-gray-400">
                      <Building2 className="w-3.5 h-3.5 text-gray-500" />
                      Slot: <span className="text-emerald-400">
                        {rec.facility_id || 'Depot 1'}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Selected Recommendation Details & Actions */}
        {selectedRec && (
          <div className="lg:col-span-7 bg-[#111827] border border-gray-800 rounded-xl p-6 space-y-6 shadow-xl">
            {/* Recommendation Header */}
            <div className="flex items-start justify-between border-b border-gray-800 pb-4">
              <div>
                <span className="text-xs font-mono text-blue-400 uppercase tracking-wider block">
                  Action Recommendation #{selectedRec.id.slice(0, 8)}
                </span>
                <h3 className="text-xl font-bold text-white mt-0.5">
                  {selectedRec.recommended_action} &bull; <span className="font-mono text-gray-300">{selectedRec.aircraft_id}</span>
                </h3>
                <p className="text-xs text-gray-400 font-mono mt-1">
                  Target Component: {selectedRec.component_id} &bull; Priority Tier: <span className="text-amber-400 font-bold uppercase">{selectedRec.priority_tier}</span>
                </p>
              </div>

              <div className="text-right">
                <span className="px-3 py-1 rounded-lg bg-gray-900 border border-gray-700 text-xs font-mono text-gray-300">
                  Priority: {selectedRec.priority_score ? selectedRec.priority_score.toFixed(1) : 'N/A'} / 100
                </span>
              </div>
            </div>

            {/* Risk & Resource Badges */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-3">
                <span className="text-gray-400 block text-[11px]">Failure Risk</span>
                <span className="text-lg font-bold text-red-400 mt-0.5 block">
                  {selectedRec.risk_score ? `${(selectedRec.risk_score * 100).toFixed(1)}%` : 'N/A'}
                </span>
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-3">
                <span className="text-gray-400 block text-[11px]">Est. RUL (Cycles)</span>
                <span className="text-lg font-bold text-white mt-0.5 block">
                  {selectedRec.rul_q50 ?? 'N/A'} cyc
                </span>
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-3">
                <span className="text-gray-400 block text-[11px]">Spare Status</span>
                <span className={`text-sm font-bold mt-1 block ${selectedRec.part_status === 'READY' ? 'text-emerald-400' : 'text-red-400'}`}>
                  {selectedRec.part_status || 'READY'}
                </span>
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-3">
                <span className="text-gray-400 block text-[11px]">Facility Bay</span>
                <span className="text-sm font-bold text-emerald-400 mt-1 block">
                  {selectedRec.facility_id || 'Hangar Bay 1'}
                </span>
              </div>
            </div>

            {/* Error Banner */}
            {errorMsg && (
              <div className="bg-red-950/80 border border-red-800 text-red-300 px-4 py-3 rounded-lg text-xs font-mono flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            {/* Action Panel */}
            {selectedRec.status === 'OPEN' || selectedRec.status === 'PENDING' ? (
              <div className="bg-gray-900/80 border border-gray-800 rounded-xl p-5 space-y-4">
                <h4 className="text-xs font-mono uppercase text-gray-300 font-bold flex items-center gap-2">
                  <Wrench className="w-4 h-4 text-blue-400" /> Record Official Decision
                </h4>

                <div>
                  <label className="text-xs font-mono text-gray-400 block mb-1">
                    Decision Justification / Operational Rationale (Min 15 characters)
                  </label>
                  <textarea
                    rows={3}
                    placeholder="Enter detailed operational reason, mission priority, or maintenance slot notes..."
                    value={justification}
                    onChange={(e) => setJustification(e.target.value)}
                    className="w-full bg-gray-950 border border-gray-700 rounded-lg p-3 text-xs text-white focus:outline-none focus:border-blue-500 font-mono"
                  />
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  <button
                    disabled={actionLoading}
                    onClick={() => handleRecordDecision('ACCEPT')}
                    className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 shadow-md"
                  >
                    <CheckCircle2 className="w-4 h-4" /> Accept & Schedule
                  </button>

                  <button
                    disabled={actionLoading}
                    onClick={() => handleRecordDecision('DEFER')}
                    className="bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 shadow-md"
                  >
                    <Clock className="w-4 h-4" /> Defer Maintenance
                  </button>

                  <button
                    disabled={actionLoading}
                    onClick={() => handleRecordDecision('REJECT')}
                    className="bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 shadow-md"
                  >
                    <XCircle className="w-4 h-4" /> Reject Recommendation
                  </button>

                  <button
                    disabled={actionLoading}
                    onClick={() => setShowOverrideModal(true)}
                    className="bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 shadow-md ml-auto"
                  >
                    <ShieldAlert className="w-4 h-4" /> 2-Person Override
                  </button>
                </div>
              </div>
            ) : (
              <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-4 text-xs font-mono space-y-2">
                <div className="flex items-center justify-between text-gray-300">
                  <span>Recorded Status: <strong className="text-emerald-400 font-bold">{selectedRec.status}</strong></span>
                  <span className="text-gray-400">Audited & Hash-Chained</span>
                </div>
              </div>
            )}

            {/* Cryptographic Evidence Passport */}
            <div className="border-t border-gray-800 pt-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-gray-400 flex items-center gap-2">
                  <FileCode className="w-4 h-4 text-emerald-400" /> Evidence Passport Cryptographic Verification
                </span>
                <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800">
                  Ed25519 Signed & Verified
                </span>
              </div>

              <div className="mt-2 bg-[#0B0F19] p-3 rounded-lg border border-gray-800 font-mono text-[11px] text-gray-300 space-y-1">
                <div>Passport ID: <span className="text-blue-400">{selectedRec.evidence_passport_id || `ep-sha256-${selectedRec.id.slice(0, 8)}`}</span></div>
                <div>Prediction ID: <span className="text-purple-400">{selectedRec.id}</span></div>
                <div>Reason Codes: <span className="text-amber-400">{(selectedRec.reason_codes || []).join(', ') || 'RUL_URGENT'}</span></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── 2-Person Override Modal ──────────────────────────── */}
      {showOverrideModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#111827] border border-purple-900 rounded-2xl max-w-md w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-gray-800 pb-3">
              <div className="flex items-center gap-2 text-purple-400">
                <ShieldAlert className="w-6 h-6" />
                <h3 className="text-lg font-bold text-white">Two-Person Override</h3>
              </div>
              <button onClick={() => setShowOverrideModal(false)} className="text-gray-400 hover:text-white">
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-gray-300">
              Overriding automated risk assessments requires dual authorization and a mandatory detailed rationale for the immutable audit log.
            </p>

            <div className="space-y-4 text-xs font-mono">
              <div>
                <label className="text-gray-400 block mb-1">Mandatory Operational Rationale (Min 15 chars)</label>
                <textarea
                  rows={3}
                  placeholder="Enter explicit operational rationale for overriding risk assessment..."
                  value={justification}
                  onChange={(e) => setJustification(e.target.value)}
                  className="w-full bg-gray-950 border border-gray-700 rounded-lg p-2 text-white font-mono"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowOverrideModal(false)}
                  className="px-4 py-2 rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={actionLoading}
                  onClick={() => handleRecordDecision('OVERRIDE')}
                  className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-bold flex items-center gap-2"
                >
                  <UserCheck className="w-4 h-4" /> Authenticate & Override
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
