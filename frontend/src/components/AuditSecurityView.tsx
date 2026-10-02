import React, { useState } from 'react';
import { 
  Lock, 
  ShieldCheck, 
  ShieldAlert, 
  FileCheck2, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle, 
  Key, 
  Server,
  KeyRound
} from 'lucide-react';
import { auditApi } from '../api/client';

interface AuditSecurityViewProps {
  posture: {
    overall_status: string;
    checks: Array<{ name: string; status: string; evidence: string }>;
    audit_chain: { status: string; total_entries: number; verified_entries: number };
  } | null;
  securityEvents: Array<{
    id: string;
    event_type: string;
    severity: string;
    description: string;
    created_at: string;
  }>;
  onRefresh: () => void;
}

export const AuditSecurityView: React.FC<AuditSecurityViewProps> = ({
  posture,
  securityEvents,
  onRefresh,
}) => {
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<any | null>(null);

  const handleVerifyChain = async () => {
    setVerifying(true);
    try {
      const res = await auditApi.verifyChain();
      setVerificationResult(res);
      onRefresh();
    } catch (err) {
      console.error(err);
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between bg-[#111827] border border-gray-800 rounded-xl p-5 shadow-lg">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Lock className="w-6 h-6 text-emerald-400" /> Cryptographic Audit & Security Posture
          </h2>
          <p className="text-xs text-gray-400 font-mono mt-1">
            SHA-256 tamper-evident hash chain &bull; Air-gap egress isolation &bull; Field-level AES-256-GCM encryption
          </p>
        </div>

        <button
          onClick={handleVerifyChain}
          disabled={verifying}
          className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-xs font-mono font-bold transition-all flex items-center gap-2 shadow-md"
        >
          <RefreshCw className={`w-4 h-4 ${verifying ? 'animate-spin' : ''}`} />
          Run Hash Chain Verification
        </button>
      </div>

      {/* Grid: Hash Chain Integrity + Security Posture */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Hash Chain Card */}
        <div className="lg:col-span-5 bg-[#111827] border border-gray-800 rounded-xl p-5 space-y-4 shadow-lg">
          <div className="flex items-center justify-between border-b border-gray-800 pb-3">
            <h3 className="text-sm font-mono uppercase text-gray-300 font-bold flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-400" /> Audit Hash Chain Status
            </h3>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
              {posture?.audit_chain.status || 'VERIFIED'}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs font-mono">
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-3">
              <span className="text-gray-400 block text-[11px]">Total Audit Records</span>
              <span className="text-xl font-bold text-white mt-1 block">
                {posture?.audit_chain.total_entries ?? 0}
              </span>
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-3">
              <span className="text-gray-400 block text-[11px]">Verified Entries</span>
              <span className="text-xl font-bold text-emerald-400 mt-1 block">
                {posture?.audit_chain.verified_entries ?? 0}
              </span>
            </div>
          </div>

          {verificationResult && (
            <div className="bg-emerald-950/60 border border-emerald-800 text-emerald-300 p-3 rounded-lg text-xs font-mono space-y-1">
              <div className="font-bold flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Verification Result: {verificationResult.status}
              </div>
              <div>Verified: {verificationResult.verified_entries} / {verificationResult.total_entries} records</div>
              <div className="text-[10px] text-emerald-400/80">
                Latest Hash: {verificationResult.latest_hash?.slice(0, 24)}...
              </div>
            </div>
          )}

          <div className="text-xs text-gray-400 font-mono space-y-2 pt-2">
            <p className="flex items-start gap-2">
              <Key className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
              <span>Each audit entry stores SHA-256(prev_hash + actor + action + payload_json + ts). Any database record mutation breaks the chain.</span>
            </p>
          </div>
        </div>

        {/* Right: Security Posture Checklist */}
        <div className="lg:col-span-7 bg-[#111827] border border-gray-800 rounded-xl p-5 space-y-4 shadow-lg">
          <h3 className="text-sm font-mono uppercase text-gray-300 font-bold flex items-center gap-2 border-b border-gray-800 pb-3">
            <Server className="w-5 h-5 text-blue-400" /> Live Security Posture Checks
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
            {posture?.checks.map((chk) => (
              <div key={chk.name} className="bg-gray-900 border border-gray-800 rounded-lg p-3 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white">{chk.name}</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    chk.status === 'PASS' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-amber-950 text-amber-400 border border-amber-800'
                  }`}>
                    {chk.status}
                  </span>
                </div>
                <p className="text-[11px] text-gray-400 leading-tight">{chk.evidence}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Security Events Table */}
      <div className="bg-[#111827] border border-gray-800 rounded-xl p-5 space-y-4 shadow-lg">
        <h3 className="text-sm font-mono uppercase text-gray-300 font-bold flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-amber-400" /> Security Audit Log & Events
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-gray-900 text-gray-400 border-b border-gray-800">
              <tr>
                <th className="p-3">Event Type</th>
                <th className="p-3">Severity</th>
                <th className="p-3">Description</th>
                <th className="p-3 text-right">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/80 text-gray-300">
              {securityEvents.map((evt) => (
                <tr key={evt.id} className="hover:bg-gray-800/40">
                  <td className="p-3 font-bold text-white">{evt.event_type}</td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      evt.severity === 'CRITICAL' ? 'bg-red-950 text-red-400 border border-red-800' :
                      evt.severity === 'HIGH' ? 'bg-amber-950 text-amber-400 border border-amber-800' :
                      'bg-blue-950 text-blue-400 border border-blue-800'
                    }`}>
                      {evt.severity}
                    </span>
                  </td>
                  <td className="p-3 text-gray-300">{evt.description}</td>
                  <td className="p-3 text-right text-gray-500 text-[11px]">
                    {evt.created_at ? new Date(evt.created_at).toLocaleString() : 'Just now'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
