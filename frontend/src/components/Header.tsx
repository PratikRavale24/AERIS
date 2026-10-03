import React from 'react';
import { 
  ShieldCheck, 
  Activity, 
  User, 
  Lock, 
  Cpu, 
  LogOut, 
  Database,
  FileCheck2,
  Sun,
  Moon,
  AlertTriangle,
  Package,
  Wrench,
  Monitor,
  BarChart3,
  Shield
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
  const [isDayTheme, setIsDayTheme] = React.useState(
    document.documentElement.getAttribute('data-theme') === 'day'
  );

  const toggleTheme = () => {
    const next = isDayTheme ? 'night' : 'day';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('ui.theme', next);
    setIsDayTheme(!isDayTheme);
  };

  const navItems = [
    { id: 'fleet', label: 'Fleet Overview', icon: Monitor, roles: ['FLEET_SUPERVISOR', 'MAINT_PLANNER', 'MAINT_ENGINEER', 'SYS_ADMIN'] },
    { id: 'recommendations', label: 'Maintenance Queue', icon: FileCheck2, roles: ['FLEET_SUPERVISOR', 'MAINT_PLANNER', 'MAINT_ENGINEER', 'SPARES_PLANNER'] },
    { id: 'spares', label: 'Spare Readiness', icon: Package, roles: ['MAINT_PLANNER', 'SPARES_PLANNER'] },
    { id: 'security', label: 'Audit & Reports', icon: Shield, roles: ['SYS_ADMIN'] },
  ];

  const filteredNav = navItems.filter((tab) => !user || tab.roles.includes(user.role));

  return (
    <header className="sticky top-0 z-40 no-print">
      {/* Classification Strip */}
      <div className="h-7 flex items-center justify-center text-xs font-semibold tracking-widest uppercase"
           style={{ backgroundColor: 'var(--color-header-bg)', color: 'var(--color-caution-text)' }}>
        <AlertTriangle className="w-3 h-3 mr-2 opacity-70" />
        PROTOTYPE — NON-OPERATIONAL DATA
      </div>

      {/* Main Command Bar */}
      <div className="border-b"
           style={{ backgroundColor: 'var(--color-bg-panel)', borderColor: 'var(--color-border)' }}>
        <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          {/* Left: Brand */}
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3 cursor-pointer select-none" onClick={() => setActiveTab('fleet')}>
              <div className="w-9 h-9 rounded-panel flex items-center justify-center"
                   style={{ backgroundColor: 'var(--color-primary-strong)' }}>
                <Activity className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-lg tracking-wide"
                        style={{ color: 'var(--color-text-primary)' }}>AERIS</span>
                  <span className="text-[10px] font-medium px-1.5 py-0.5 rounded"
                        style={{ backgroundColor: 'var(--color-bg-inset)', color: 'var(--color-text-muted)', border: '1px solid var(--color-border-subtle)' }}>
                    SIH26249
                  </span>
                </div>
                <p className="text-[11px]" style={{ color: 'var(--color-text-muted)' }}>
                  Aircraft Reliability & Intelligence System
                </p>
              </div>
            </div>

            {/* Navigation */}
            <nav className="hidden lg:flex items-center gap-1 ml-2">
              {filteredNav.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className="px-3 py-2 rounded-panel text-[13px] font-medium flex items-center gap-2"
                    style={{
                      backgroundColor: isActive ? 'var(--color-bg-hover)' : 'transparent',
                      color: isActive ? 'var(--color-primary)' : 'var(--color-text-secondary)',
                      borderLeft: isActive ? '3px solid var(--color-primary)' : '3px solid transparent',
                    }}
                  >
                    <Icon className="w-4 h-4" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Right Controls */}
          <div className="flex items-center gap-3">
            {/* Security Indicators */}
            <div className="hidden md:flex items-center gap-2">
              <div className="flex items-center gap-1.5 px-2 py-1 rounded text-[11px] font-medium"
                   style={{ backgroundColor: 'var(--color-bg-inset)', color: 'var(--color-ok-text)', border: '1px solid var(--color-border-subtle)' }}>
                <ShieldCheck className="w-3 h-3" />
                <span>Audit: {securityStatus?.chainStatus || 'VERIFIED'}</span>
              </div>
              <div className="flex items-center gap-1.5 px-2 py-1 rounded text-[11px] font-medium"
                   style={{ backgroundColor: 'var(--color-bg-inset)', color: 'var(--color-advisory-text)', border: '1px solid var(--color-border-subtle)' }}>
                <Lock className="w-3 h-3" />
                <span>Local</span>
              </div>
            </div>

            {/* Model Cards */}
            <button
              onClick={onOpenModelCards}
              className="hidden sm:flex items-center gap-1.5 px-2 py-1.5 rounded text-[11px] font-medium"
              style={{ color: 'var(--color-text-muted)' }}
              title="AI Model Cards"
            >
              <Cpu className="w-3.5 h-3.5" /> Models
            </button>

            {/* Theme Toggle */}
            <button onClick={toggleTheme} className="p-1.5 rounded"
                    style={{ color: 'var(--color-text-muted)' }}
                    title={isDayTheme ? 'Switch to Night Mode' : 'Switch to Day Mode'}>
              {isDayTheme ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
            </button>

            {/* User Area */}
            {user ? (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-panel"
                   style={{ backgroundColor: 'var(--color-bg-inset)', border: '1px solid var(--color-border-subtle)' }}>
                <div className="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold text-white uppercase"
                     style={{ backgroundColor: 'var(--color-primary-strong)' }}>
                  {user.username.slice(0, 2)}
                </div>
                <div className="hidden md:block text-left">
                  <div className="text-[12px] font-semibold" style={{ color: 'var(--color-text-primary)' }}>{user.username}</div>
                  <div className="text-[10px] uppercase font-medium" style={{ color: 'var(--color-text-muted)' }}>{user.role.replace(/_/g, ' ')}</div>
                </div>
                <button
                  onClick={onLogout}
                  title="Sign Out"
                  className="p-1 rounded ml-1"
                  style={{ color: 'var(--color-text-muted)' }}
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={onOpenLogin}
                className="px-4 py-1.5 rounded-panel text-sm font-medium text-white"
                style={{ backgroundColor: 'var(--color-primary-strong)' }}
              >
                <User className="w-4 h-4 inline mr-1.5" />
                Sign In
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
