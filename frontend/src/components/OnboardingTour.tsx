import React, { useState, useEffect } from 'react';

interface OnboardingTourProps {
  userRole: string;
}

export const OnboardingTour: React.FC<OnboardingTourProps> = ({ userRole }) => {
  const [run, setRun] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const tourKey = `aeris_tour_completed_${userRole}`;
    if (!localStorage.getItem(tourKey)) {
      setRun(true);
    }
  }, [userRole]);

  const steps = [
    {
      title: 'Welcome to AERIS',
      content: 'This is your intelligence-driven aircraft reliability system. Let\'s take a quick tour to help you get started.',
    },
    ...(userRole === 'FLEET_SUPERVISOR' ? [
      {
        title: 'Fleet Overview',
        content: 'Monitor the readiness and risk levels of all your aircraft at a glance.',
      },
      {
        title: 'Maintenance Queue',
        content: 'Review AI-generated maintenance recommendations and securely authorize operational decisions.',
      }
    ] : userRole === 'MAINT_PLANNER' || userRole === 'MAINT_ENGINEER' ? [
      {
        title: 'Maintenance Queue',
        content: 'Your primary workspace. Review AI risk assessments and provide operational rationale.',
      },
      {
        title: 'Spare Readiness',
        content: 'Check component availability and depot capacity before scheduling maintenance.',
      }
    ] : userRole === 'SYS_ADMIN' ? [
      {
        title: 'Audit & Reports',
        content: 'The Audit dashboard provides a real-time look at cryptographic integrity and security events.',
      }
    ] : [
      {
        title: 'Fleet Overview',
        content: 'Monitor fleet health and analytics from this main dashboard.',
      }
    ])
  ];

  if (!run) return null;

  const handleNext = () => {
    if (currentStep === steps.length - 1) {
      setRun(false);
      localStorage.setItem(`aeris_tour_completed_${userRole}`, 'true');
    } else {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handleSkip = () => {
    setRun(false);
    localStorage.setItem(`aeris_tour_completed_${userRole}`, 'true');
  };

  const step = steps[currentStep];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-300">
      <div className="w-[400px] p-6 rounded-xl shadow-2xl flex flex-col gap-4" style={{ backgroundColor: 'var(--color-bg-panel)', border: '1px solid var(--color-border)' }}>
        <div>
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-lg font-bold text-white">{step.title}</h3>
            <span className="text-xs font-semibold px-2 py-1 rounded-full" style={{ backgroundColor: 'var(--color-bg-inset)', color: 'var(--color-text-muted)' }}>
              {currentStep + 1} / {steps.length}
            </span>
          </div>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
            {step.content}
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
    </div>
  );
};
