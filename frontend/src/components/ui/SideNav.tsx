import React from 'react';
import { Activity, Shield, AlertTriangle, PenTool, BrainCircuit, FileSearch, Database, ShieldAlert, Users, LogOut, Moon, Sun, Monitor } from 'lucide-react';

interface SideNavProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  role: string;
}

export const SideNav: React.FC<SideNavProps> = ({ activeTab, setActiveTab, role }) => {
  const allowed = (roles: string[]) => roles.includes(role);

  return (
    <nav className="w-56 bg-panel border-r border-border-strong flex flex-col h-full overflow-y-auto">
      <div className="flex-1 py-4">
        {/* SITUATION */}
        <div className="mb-6">
          <div className="px-4 mb-2 text-[10px] font-condensed font-bold text-muted uppercase tracking-wider">Situation</div>
          {allowed(['FLEET_SUPERVISOR', 'MAINT_PLANNER', 'MAINT_ENGINEER', 'SYS_ADMIN']) && (
            <NavItem 
              icon={<Monitor className="w-4 h-4" />} 
              label="Fleet Overview" 
              active={activeTab === 'fleet'} 
              onClick={() => setActiveTab('fleet')} 
            />
          )}
        </div>

        {/* MAINTENANCE */}
        <div className="mb-6">
          <div className="px-4 mb-2 text-[10px] font-condensed font-bold text-muted uppercase tracking-wider">Maintenance</div>
          {allowed(['MAINT_PLANNER', 'MAINT_ENGINEER', 'FLEET_SUPERVISOR', 'SPARES_PLANNER']) && (
            <NavItem 
              icon={<AlertTriangle className="w-4 h-4" />} 
              label="Decision Support" 
              active={activeTab === 'recommendations'} 
              onClick={() => setActiveTab('recommendations')} 
            />
          )}
          {allowed(['SPARES_PLANNER', 'MAINT_PLANNER']) && (
            <NavItem 
              icon={<PenTool className="w-4 h-4" />} 
              label="Spares & Logistics" 
              active={activeTab === 'spares'} 
              onClick={() => setActiveTab('spares')} 
            />
          )}
        </div>

        {/* GOVERNANCE */}
        <div className="mb-6">
          <div className="px-4 mb-2 text-[10px] font-condensed font-bold text-muted uppercase tracking-wider">Governance</div>
          {allowed(['SYS_ADMIN']) && (
            <NavItem 
              icon={<ShieldAlert className="w-4 h-4" />} 
              label="Audit & Posture" 
              active={activeTab === 'security'} 
              onClick={() => setActiveTab('security')} 
            />
          )}
        </div>
      </div>
    </nav>
  );
};

const NavItem: React.FC<{ icon: React.ReactNode; label: string; active: boolean; onClick: () => void }> = ({ icon, label, active, onClick }) => {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-4 py-2 text-[13px] font-medium transition-colors border-l-[3px] ${
        active 
          ? 'bg-hover border-primary text-primary' 
          : 'border-transparent text-content-secondary hover:bg-hover hover:text-content-primary'
      }`}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
};
