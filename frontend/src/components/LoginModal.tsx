import React, { useState } from 'react';
import { X, User, Lock, ShieldCheck, KeyRound, Check } from 'lucide-react';
import { authApi } from '../api/client';

interface LoginModalProps {
  onClose: () => void;
  onLoginSuccess: (user: { username: string; role: string }) => void;
}

const DEMO_ROLES = [
  { username: 'commander1', role: 'commander', label: 'Air Base Commander', desc: 'Full fleet visibility, operational release approval' },
  { username: 'supervisor1', role: 'supervisor', label: 'Maintenance Supervisor', desc: 'Accept/Defer recommendations, two-person override' },
  { username: 'engineer1', role: 'engineer', label: 'Flight Test Engineer', desc: 'Telemetry analysis, sensor diagnostics' },
  { username: 'logistics1', role: 'logistics', label: 'Supply Chain Officer', desc: 'Spares inventory, lead-time management' },
  { username: 'auditor1', role: 'auditor', label: 'Security Auditor', desc: 'Cryptographic hash chain & compliance verification' },
];

export const LoginModal: React.FC<LoginModalProps> = ({ onClose, onLoginSuccess }) => {
  const [selectedRole, setSelectedRole] = useState(DEMO_ROLES[1]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (username: string, role: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await authApi.login(username, role);
      onLoginSuccess({ username: data.user.username, role: data.user.role });
      onClose();
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#111827] border border-gray-800 rounded-2xl max-w-lg w-full p-6 space-y-6 shadow-2xl">
        <div className="flex items-center justify-between border-b border-gray-800 pb-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-blue-400" />
            <h3 className="text-lg font-bold text-white">Select Persona & Authenticate</h3>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-xs text-gray-300">
          AERIS implements Role-Based Access Control (RBAC). Select a demo persona to authenticate and test server-side permission checks.
        </p>

        {error && (
          <div className="bg-red-950/80 border border-red-800 text-red-300 p-3 rounded-lg text-xs font-mono">
            {error}
          </div>
        )}

        <div className="space-y-2">
          {DEMO_ROLES.map((r) => {
            const isSelected = selectedRole.username === r.username;
            return (
              <button
                key={r.username}
                onClick={() => {
                  setSelectedRole(r);
                  handleLogin(r.username, `Demo${r.username}Pass123!`);
                }}
                disabled={loading}
                className={`w-full p-3.5 rounded-xl border text-left transition-all flex items-center justify-between ${
                  isSelected
                    ? 'bg-blue-950/50 border-blue-500 text-white shadow-lg'
                    : 'bg-gray-900/60 border-gray-800 text-gray-300 hover:bg-gray-800'
                }`}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-white">{r.label}</span>
                    <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-blue-900/60 text-blue-300">
                      {r.role}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 font-mono mt-0.5">{r.desc}</p>
                </div>

                <div className="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs">
                  <Check className="w-3.5 h-3.5" />
                </div>
              </button>
            );
          })}
        </div>

        <div className="text-[11px] text-gray-500 font-mono text-center pt-2 border-t border-gray-800">
          Argon2id password hashing &bull; Session cookies with HttpOnly, SameSite=Strict, __Host- prefix
        </div>
      </div>
    </div>
  );
};
