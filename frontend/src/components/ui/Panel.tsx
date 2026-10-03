import React from 'react';

interface PanelProps {
  title?: string;
  index?: string | number;
  lastUpdated?: string;
  children: React.ReactNode;
  className?: string;
  action?: React.ReactNode;
}

export const Panel: React.FC<PanelProps> = ({ title, index, lastUpdated, children, className = '', action }) => {
  return (
    <div className={`relative bg-panel border border-border rounded-[2px] ${className}`}>
      {/* Corner Ticks */}
      <div className="absolute top-0 left-0 w-1 h-1 border-t border-l border-border-strong rounded-tl-[2px]" />
      <div className="absolute bottom-0 right-0 w-1 h-1 border-b border-r border-border-strong rounded-br-[2px]" />

      {/* Header */}
      {(title || lastUpdated || action) && (
        <div className="flex items-center justify-between px-3 py-2 bg-raised border-b border-border-subtle rounded-t-[2px]">
          <div className="flex items-center gap-2">
            {index && <span className="text-muted font-mono text-[10px] bg-inset px-1.5 rounded-sm">{index}</span>}
            {title && <h3 className="text-[12px] font-condensed font-semibold text-content-primary uppercase tracking-wider">{title}</h3>}
          </div>
          <div className="flex items-center gap-3">
            {lastUpdated && <span className="text-[10px] font-mono text-muted uppercase">UPDATED: {lastUpdated}</span>}
            {action && <div>{action}</div>}
          </div>
        </div>
      )}

      {/* Content */}
      <div className="p-4">
        {children}
      </div>
    </div>
  );
};
