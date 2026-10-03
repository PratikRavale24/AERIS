import React, { useState, useEffect, useCallback } from 'react';

interface OnboardingTourProps {
  userRole: string;
  setActiveTab: (tab: string) => void;
}

export const OnboardingTour: React.FC<OnboardingTourProps> = ({ userRole, setActiveTab }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [run, setRun] = useState(false);
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);

  useEffect(() => {
    const tourKey = `aeris_tour_completed_${userRole}`;
    if (!localStorage.getItem(tourKey)) {
      setTimeout(() => setRun(true), 500);
    }
  }, [userRole]);

  const steps = userRole === 'FLEET_SUPERVISOR' ? [
    { element: '.tour-fleet', title: 'Fleet Overview', desc: 'Monitor the readiness and risk levels of all your aircraft.', action: null },
    { element: '.tour-kpi-row', title: 'Key Metrics', desc: 'These KPIs highlight critical shortages and high-risk assets requiring immediate attention.', action: null },
    { element: null, title: 'Switching Views', desc: 'Now let\'s look at the Maintenance Queue to record decisions.', action: () => setActiveTab('recommendations') },
    { element: '.tour-record-decision', title: 'Interactive Workspace', desc: 'Go ahead, you can actually type an operational rationale and click Accept to see the system record your decision securely!', action: null }
  ] : userRole === 'MAINT_PLANNER' || userRole === 'MAINT_ENGINEER' ? [
    { element: null, title: 'Maintenance Queue', desc: 'Your primary workspace. Let\'s review AI risk assessments.', action: () => setActiveTab('recommendations') },
    { element: '.tour-record-decision', title: 'Operational Rationale', desc: 'Authorize AI recommendations by providing reasoning. Try typing a rationale and clicking Accept!', action: null },
    { element: '.tour-evidence', title: 'Cryptographic Audit', desc: 'Every recommendation is backed by a verifiable SHA-256 evidence passport to ensure data integrity.', action: null }
  ] : userRole === 'SYS_ADMIN' ? [
    { element: null, title: 'System Admin', desc: 'Welcome to the Audit dashboard. Let me pull that up for you.', action: () => setActiveTab('security') },
    { element: '.tour-security', title: 'Live Security Posture', desc: 'Monitor real-time cryptographic integrity and air-gapped egress isolation.', action: null }
  ] : [
    { element: null, title: 'Welcome to AERIS', desc: 'This is your intelligence-driven aircraft reliability system.', action: null }
  ];

  const updateRect = useCallback(() => {
    if (!run || currentStep >= steps.length) return;
    const step = steps[currentStep];
    if (step.element) {
      const el = document.querySelector(step.element);
      if (el) {
        setTargetRect(el.getBoundingClientRect());
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        (el as HTMLElement).style.position = 'relative';
        (el as HTMLElement).style.zIndex = '999999';
        (el as HTMLElement).style.pointerEvents = 'auto'; // allow clicking
        return;
      }
    }
    setTargetRect(null);
  }, [run, currentStep, steps]);

  useEffect(() => {
    window.addEventListener('resize', updateRect);
    return () => window.removeEventListener('resize', updateRect);
  }, [updateRect]);

  useEffect(() => {
    const interval = setInterval(updateRect, 200);
    return () => clearInterval(interval);
  }, [updateRect]);

  const cleanupPrev = () => {
    const prevStep = steps[currentStep];
    if (prevStep && prevStep.element) {
      const el = document.querySelector(prevStep.element);
      if (el) {
        (el as HTMLElement).style.position = '';
        (el as HTMLElement).style.zIndex = '';
        (el as HTMLElement).style.pointerEvents = '';
      }
    }
  };

  const handleNext = () => {
    cleanupPrev();
    if (currentStep === steps.length - 1) {
      setRun(false);
      localStorage.setItem(`aeris_tour_completed_${userRole}`, 'true');
    } else {
      const nextStep = steps[currentStep + 1];
      if (nextStep.action) {
        nextStep.action();
      }
      setCurrentStep(prev => prev + 1);
    }
  };

  const handleSkip = () => {
    cleanupPrev();
    setRun(false);
    localStorage.setItem(`aeris_tour_completed_${userRole}`, 'true');
  };

  if (!run || currentStep >= steps.length) return null;

  const step = steps[currentStep];

  // Calculate popover position
  let popoverTop = '50%';
  let popoverLeft = '50%';
  let transform = 'translate(-50%, -50%)';

  if (targetRect) {
    // Try placing below the element
    popoverTop = `${targetRect.bottom + 20}px`;
    popoverLeft = `${targetRect.left + (targetRect.width / 2)}px`;
    transform = 'translate(-50%, 0)';
    
    // If it goes off screen bottom, put it above
    if (targetRect.bottom + 200 > window.innerHeight) {
      popoverTop = `${targetRect.top - 20}px`;
      transform = 'translate(-50%, -100%)';
    }
  }

  return (
    <>
      {/* Dynamic Overlay Shadow */}
      <div 
        style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          zIndex: 999998,
          pointerEvents: targetRect ? 'none' : 'auto', // If no target, block all clicks behind
          background: targetRect ? 'transparent' : 'rgba(0,0,0,0.7)',
          boxShadow: targetRect 
            ? `0 0 0 9999px rgba(0,0,0,0.7) inset, 0 0 0 9999px rgba(0,0,0,0.7)` 
            : 'none',
          clipPath: targetRect 
            ? `polygon(0% 0%, 0% 100%, ${targetRect.left - 10}px 100%, ${targetRect.left - 10}px ${targetRect.top - 10}px, ${targetRect.right + 10}px ${targetRect.top - 10}px, ${targetRect.right + 10}px ${targetRect.bottom + 10}px, ${targetRect.left - 10}px ${targetRect.bottom + 10}px, ${targetRect.left - 10}px 100%, 100% 100%, 100% 0%)`
            : 'none',
          transition: 'all 0.3s ease'
        }}
      />
      
      {/* Popover */}
      <div 
        className="fixed p-6 rounded-xl shadow-2xl flex flex-col gap-4 w-[350px] animate-in fade-in zoom-in duration-300"
        style={{ 
          backgroundColor: 'var(--color-bg-panel)', 
          border: '1px solid var(--color-border)',
          zIndex: 999999,
          top: popoverTop,
          left: popoverLeft,
          transform: transform,
          transition: 'top 0.3s ease, left 0.3s ease'
        }}
      >
        <div>
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-lg font-bold text-white">{step.title}</h3>
            <span className="text-xs font-semibold px-2 py-1 rounded-full" style={{ backgroundColor: 'var(--color-bg-inset)', color: 'var(--color-text-muted)' }}>
              {currentStep + 1} / {steps.length}
            </span>
          </div>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
            {step.desc}
          </p>
        </div>
        
        <div className="flex justify-between mt-4">
          <button 
            onClick={handleSkip}
            className="text-sm font-medium hover:text-white transition-colors"
            style={{ color: 'var(--color-text-muted)' }}
          >
            Skip Tour
          </button>
          
          <button 
            onClick={handleNext}
            className="px-4 py-2 text-sm font-medium text-white rounded-lg transition-transform hover:scale-105 active:scale-95"
            style={{ backgroundColor: 'var(--color-primary-strong)' }}
          >
            {currentStep === steps.length - 1 ? 'Get Started' : 'Next'}
          </button>
        </div>
      </div>
    </>
  );
};
