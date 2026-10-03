import React from 'react';
import { StatusGlyph, StatusType } from './StatusGlyph';

interface StatusBadgeProps {
  status: StatusType;
  label: string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label, className = '' }) => {
  const getColors = () => {
    switch(status) {
      case 'ok': return 'bg-ok/10 text-ok border-ok/30';
      case 'advisory': return 'bg-advisory/10 text-advisory border-advisory/30';
      case 'caution': return 'bg-caution/10 text-caution border-caution/30';
      case 'high': return 'bg-high/10 text-high border-high/30';
      case 'critical': return 'bg-critical/10 text-critical border-critical/30';
      case 'simulation': return 'bg-simulation/10 text-simulation border-simulation/30';
    }
  };

  return (
    <div className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-[2px] border ${getColors()} font-condensed uppercase text-[11px] tracking-wider font-semibold ${className}`}>
      <StatusGlyph status={status} />
      {label}
    </div>
  );
};
