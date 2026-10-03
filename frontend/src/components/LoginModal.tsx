import React, { useState } from 'react';
import { X, Lock, Shield, User, KeyRound, Loader2 } from 'lucide-react';
import { authApi } from '../api/client';

interface LoginModalProps {
  onClose: () => void;
  onLoginSuccess: (user: { username: string; role: string }) => void;
}

export const LoginModal: React.FC<LoginModalProps> = ({ onClose, onLoginSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      setError('Please enter both username and password.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await authApi.login(username, password);
      onLoginSuccess({ username: data.user.username, role: data.user.role });
      onClose();
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const fillDemoCreds = (user: string) => {
    setUsername(user);
    setPassword(`Demo${user}Pass123!`);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
         style={{ backgroundColor: 'rgba(8,12,18,0.85)' }}>
      <div className="w-full max-w-lg rounded-panel overflow-hidden"
           style={{ backgroundColor: 'var(--color-bg-panel)', border: '1px solid var(--color-border)', boxShadow: 'var(--shadow-modal)' }}>
        
        {/* Top accent */}
        <div className="h-1" style={{ backgroundColor: 'var(--color-primary-strong)' }} />

        <div className="p-8">
          {/* Header */}
          <div className="flex items-start justify-between mb-8">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Shield className="w-5 h-5" style={{ color: 'var(--color-primary)' }} />
              </div>
              <h2 className="text-xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
                AERIS
              </h2>
              <p className="text-[13px] mt-1" style={{ color: 'var(--color-text-secondary)' }}>
                Aircraft Reliability & Intelligence System
              </p>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="p-3 rounded-panel text-[13px] mb-6 flex items-start gap-2"
                 style={{ backgroundColor: 'var(--color-bg-inset)', color: 'var(--color-critical-text)', border: '1px solid var(--color-critical)' }}>
              <Lock className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="text-[13px] font-medium flex items-center gap-2 mb-1.5"
                     style={{ color: 'var(--color-text-secondary)' }}>
                <User className="w-4 h-4" style={{ color: 'var(--color-text-muted)' }} /> Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={loading}
                className="w-full px-3 py-2.5 rounded-panel text-[14px] outline-none"
                style={{
                  backgroundColor: 'var(--color-bg-inset)',
                  border: '1px solid var(--color-border)',
                  color: 'var(--color-text-primary)',
                }}
                placeholder="e.g. commander1"
              />
            </div>

            <div>
              <label className="text-[13px] font-medium flex items-center gap-2 mb-1.5"
                     style={{ color: 'var(--color-text-secondary)' }}>
                <KeyRound className="w-4 h-4" style={{ color: 'var(--color-text-muted)' }} /> Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                className="w-full px-3 py-2.5 rounded-panel text-[14px] outline-none"
                style={{
                  backgroundColor: 'var(--color-bg-inset)',
                  border: '1px solid var(--color-border)',
                  color: 'var(--color-text-primary)',
                }}
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-panel text-sm font-semibold text-white flex items-center justify-center gap-2 disabled:opacity-60"
              style={{ backgroundColor: 'var(--color-primary-strong)' }}
            >
              {loading ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Authenticating...</>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {/* Demo Accounts */}
          <div className="mt-6 pt-5" style={{ borderTop: '1px solid var(--color-border-subtle)' }}>
            <p className="text-[11px] font-medium mb-2" style={{ color: 'var(--color-text-muted)' }}>
              Demo Accounts (click to fill):
            </p>
            <div className="flex flex-wrap gap-2">
              {['commander1', 'supervisor1', 'engineer1', 'logistics1', 'auditor1'].map((name) => (
                <button key={name} onClick={() => fillDemoCreds(name)} type="button"
                  className="text-[11px] px-2 py-1 rounded font-medium capitalize"
                  style={{ backgroundColor: 'var(--color-bg-inset)', color: 'var(--color-text-secondary)', border: '1px solid var(--color-border-subtle)' }}>
                  {name.replace('1', '')}
                </button>
              ))}
            </div>
          </div>

          {/* Safety Statement */}
          <p className="text-[10px] text-center mt-6 leading-relaxed"
             style={{ color: 'var(--color-text-muted)' }}>
            This system is a maintenance decision-support prototype. Predictions are not airworthiness or release-to-service decisions and are not validated for operational aircraft.
          </p>
        </div>
      </div>
    </div>
  );
};
