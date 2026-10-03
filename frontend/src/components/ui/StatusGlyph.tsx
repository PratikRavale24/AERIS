import React from 'react';

export type StatusType = 'ok' | 'advisory' | 'caution' | 'high' | 'critical' | 'simulation';

export const StatusGlyph: React.FC<{ status: StatusType; className?: string }> = ({ status, className = '' }) => {
  const baseClasses = `inline-block shrink-0 ${className}`;
  
  switch (status) {
    case 'ok':
      return <div className={`${baseClasses} w-3 h-3 rounded-full bg-ok`} />;
    case 'advisory':
      return <div className={`${baseClasses} w-3 h-3 rounded-full border-2 border-advisory`} />;
    case 'caution':
      return (
        <div className={`${baseClasses} w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-b-[10px] border-b-caution`} />
      );
    case 'high':
      return <div className={`${baseClasses} w-3 h-3 bg-high transform rotate-45`} />;
    case 'critical':
      return (
        <div className={`${baseClasses} w-3 h-3 bg-critical flex items-center justify-center`}>
          <span className="text-[8px] font-bold text-white">!</span>
        </div>
      );
    case 'simulation':
      return (
        <div className={`${baseClasses} w-3 h-3 bg-simulation opacity-80`} style={{ backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 2px, rgba(255,255,255,0.3) 2px, rgba(255,255,255,0.3) 4px)' }} />
      );
    default:
      return null;
  }
};
