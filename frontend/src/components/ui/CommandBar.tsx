import React, { useEffect, useState } from 'react';
import { LogOut, HelpCircle, Moon, Sun } from 'lucide-react';
import { StatusBadge } from './StatusBadge';

interface CommandBarProps {
  user: { username: string; role: string };
  title: string;
  onLogout: () => void;
}

export const CommandBar: React.FC<CommandBarProps> = ({ user, title, onLogout }) => {
  const [time, setTime] = useState(new Date());
  const [isDay, setIsDay] = useState(document.documentElement.getAttribute('data-theme') === 'day');

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const toggleTheme = () => {
    const newTheme = isDay ? 'night' : 'day';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('ui.theme', newTheme);
    setIsDay(!isDay);
  };

  const getDtg = (d: Date) => {
    const pad = (n: number) => n.toString().padStart(2, '0');
    const day = pad(d.getUTCDate());
    const hrs = pad(d.getUTCHours());
    const min = pad(d.getUTCMinutes());
    const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
    const month = months[d.getUTCMonth()];
    const yr = d.getUTCFullYear().toString().slice(-2);
    return `${day}${hrs}${min}Z ${month} ${yr}`;
  };

  return (
    <div className="h-12 bg-header border-b border-border-strong flex items-center justify-between px-4 text-content-primary w-full">
      <div className="flex items-center gap-4">
        {/* Abstract Wordmark */}
        <div className="flex items-center gap-2">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M4 12L12 4L20 12M4 20L12 12L20 20" stroke="currentColor" strokeWidth="2" strokeLinecap="square" strokeLinejoin="miter"/>
          </svg>
          <span className="font-condensed font-bold text-[14px] tracking-wide uppercase">AERIS-PDM</span>
        </div>
        <div className="h-4 w-px bg-border-strong mx-2" />
        <span className="font-condensed font-semibold text-[13px] text-content-secondary uppercase">{title}</span>
      </div>

      <div className="flex items-center gap-4">
        <div className="font-mono text-[12px] text-primary bg-bg-inset px-2 py-1 rounded-[2px] border border-border-subtle tracking-tight">
          {getDtg(time)}
        </div>
        
        <StatusBadge status="ok" label="SECURE" className="hidden sm:flex" />

        <div className="flex items-center gap-2 bg-bg-inset px-2 py-1 rounded-[2px] border border-border-subtle">
          <span className="text-[12px] font-semibold">{user.username}</span>
          <span className="text-[10px] font-condensed font-bold text-muted uppercase bg-bg-panel px-1 rounded-sm border border-border">{user.role}</span>
        </div>

        <button onClick={toggleTheme} className="text-content-secondary hover:text-content-primary transition-colors" aria-label="Toggle Theme">
          {isDay ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
        </button>

        <button onClick={onLogout} className="text-content-secondary hover:text-critical transition-colors" aria-label="Logout">
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
