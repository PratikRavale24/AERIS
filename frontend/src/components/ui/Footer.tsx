import React from 'react';
import { Info } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="h-8 bg-bg-canvas border-t border-border flex items-center justify-center px-4 shrink-0 w-full">
      <div className="flex items-center gap-2 text-[11px] text-content-secondary max-w-4xl text-center">
        <Info className="w-3 h-3 shrink-0" />
        <span>This system is a maintenance decision-support prototype. Predictions are not airworthiness or release-to-service decisions and are not validated for operational aircraft.</span>
      </div>
    </footer>
  );
};
