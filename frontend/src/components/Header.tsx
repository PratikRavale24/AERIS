import React from 'react';
import { 
  ShieldCheck, 
  ShieldAlert, 
  Activity, 
  User, 
  Lock, 
  Cpu, 
  LogOut, 
  Database,
  Radio,
  FileCheck2
} from 'lucide-react';

interface HeaderProps {
  user: { username: string; role: string } | null;
  onOpenLogin: () => void;
  onLogout: () => void;
  onOpenModelCards: () => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  securityStatus: { chainStatus: string; egressBlocked: boolean } | null;
}

export const Header: React.FC<HeaderProps> = ({
  user,
  onOpenLogin,
  onLogout,
  onOpenModelCards,
  activeTab,
  setActiveTab,
  securityStatus,
}) => {
  return (
    <header className="bg-[#111827] border-b border-gray-800 sticky top-0 z-40 shadow-xl">
      {/* Top Banner — Disclaimer */}
      <div className="bg-amber-950/60 border-b border-amber-800/40 text-amber-300 px-4 py-1 text-xs font-mono flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
          <span className="font-semibold uppercase tracking-wider">AERIS Decision-Support Prototype</span>
          <span className="hidden md:inline text-amber-400/80">
            | Synthetic Non-Operational Data | Predictions are recommendations, not airworthiness releases
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-amber-400/80 hidden sm:inline">Classification: UNCLASSIFIED / DEMO</span>
          <button 
            onClick={onOpenModelCards}
            className="hover:underline flex items-center gap-1 text-blue-400 font-sans text-xs font-medium"
          >
            <Cpu className="w-3 h-3" /> Model Cards & Audit
          </button>
        </div>
      </div>

      {/* Main Navigation Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand / Logo */}
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setActiveTab('fleet')}>
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center shadow-lg shadow-blue-950">
              <Radio className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-xl tracking-wider text-white">AERIS</span>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-blue-900/60 text-blue-300 border border-blue-700/50">
                  v0.1.0
                </span>
              </div>
              <p className="text-[11px] text-gray-400 font-mono tracking-tight">Fleet Health & Predictive Maintenance</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden lg:flex items-center gap-1 ml-4">
            {[
              { id: 'fleet', label: 'Fleet Overview', icon: Activity },
              { id: 'recommendations', label: 'Decision Support', icon: FileCheck2 },
              { id: 'spares', label: 'Supply & Facilities', icon: Database },
              { id: 'security', label: 'Audit & Posture', icon: Lock },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-all flex items-center gap-2 ${
                    isActive
                      ? 'bg-blue-600/20 text-blue-400 border border-blue-500/40 shadow-inner'
                      : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Right Controls: Security Posture & User Badge */}
        <div className="flex items-center gap-4">
          {/* Security Status Pills */}
          <div className="hidden sm:flex items-center gap-2">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono bg-emerald-950/60 border border-emerald-800/50 text-emerald-400">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Chain: {securityStatus?.chainStatus || 'VERIFIED'}</span>
            </div>
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono bg-blue-950/60 border border-blue-800/50 text-blue-400">
              <Lock className="w-3.5 h-3.5" />
              <span>Air-Gapped</span>
            </div>
          </div>

          {/* User Profile / Login */}
          {user ? (
            <div className="flex items-center gap-3 bg-gray-800/80 border border-gray-700 rounded-lg px-3 py-1.5">
              <div className="w-7 h-7 rounded-full bg-blue-700 text-white flex items-center justify-center text-xs font-bold uppercase">
                {user.username.slice(0, 2)}
              </div>
              <div className="text-left hidden md:block">
                <div className="text-xs font-semibold text-white">{user.username}</div>
                <div className="text-[10px] text-blue-400 uppercase font-mono">{user.role}</div>
              </div>
              <button
                onClick={onLogout}
                title="Sign Out"
                className="text-gray-400 hover:text-red-400 transition-colors p-1"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={onOpenLogin}
              className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-1.5 rounded-lg text-sm font-medium transition-all shadow-md flex items-center gap-2"
            >
              <User className="w-4 h-4" />
              Sign In
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
