import React from 'react';
import { ClassificationStrip } from './ClassificationStrip';
import { CommandBar } from './CommandBar';
import { SideNav } from './SideNav';
import { Footer } from './Footer';

interface AppShellProps {
  user: { username: string; role: string };
  onLogout: () => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ user, onLogout, activeTab, setActiveTab, children }) => {
  const getTitle = () => {
    switch (activeTab) {
      case 'fleet': return 'Fleet Overview';
      case 'recommendations': return 'Decision Support';
      case 'spares': return 'Spares & Logistics';
      case 'security': return 'Audit & Posture';
      default: return 'Module';
    }
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-canvas text-content-primary font-sans">
      <ClassificationStrip />
      <CommandBar user={user} title={getTitle()} onLogout={onLogout} />
      
      <div className="flex flex-1 overflow-hidden">
        <SideNav activeTab={activeTab} setActiveTab={setActiveTab} role={user.role} />
        <main className="flex-1 overflow-y-auto overflow-x-hidden p-4 lg:p-6 bg-canvas relative">
          <div className="max-w-[1920px] mx-auto w-full h-full">
            {children}
          </div>
        </main>
      </div>

      <Footer />
    </div>
  );
};
