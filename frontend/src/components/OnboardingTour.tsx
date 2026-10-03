import React, { useState, useEffect } from 'react';
import Joyride, { Step, CallBackProps, STATUS } from 'react-joyride';

interface OnboardingTourProps {
  userRole: string;
}

export const OnboardingTour: React.FC<OnboardingTourProps> = ({ userRole }) => {
  const [run, setRun] = useState(false);
  const [steps, setSteps] = useState<Step[]>([]);

  useEffect(() => {
    // Only run the tour if it hasn't been completed for this role
    const tourKey = `aeris_tour_completed_${userRole}`;
    if (!localStorage.getItem(tourKey)) {
      setRun(true);
    }

    const commonSteps: Step[] = [
      {
        target: 'body',
        content: 'Welcome to AERIS! This is your intelligence-driven aircraft reliability system. Let\'s take a quick tour.',
        placement: 'center',
        disableBeacon: true,
      }
    ];

    let roleSteps: Step[] = [];

    if (userRole === 'FLEET_SUPERVISOR') {
      roleSteps = [
        {
          target: '.tour-fleet-overview',
          content: 'Here is your Fleet Overview. You can instantly see the readiness and risk levels of all your monitored aircraft.',
          placement: 'bottom',
        },
        {
          target: '.tour-kpi-row',
          content: 'These KPIs highlight critical shortages and high-risk assets requiring immediate attention.',
          placement: 'bottom',
        },
        {
          target: '.tour-recommendations',
          content: 'Switch to the Maintenance Queue to review AI-generated maintenance recommendations and record dual-authorized decisions.',
          placement: 'bottom',
        }
      ];
    } else if (userRole === 'MAINT_PLANNER' || userRole === 'MAINT_ENGINEER') {
      roleSteps = [
        {
          target: '.tour-recommendations',
          content: 'The Maintenance Queue is your primary workspace. Review AI risk assessments and operational rationale.',
          placement: 'bottom',
        },
        {
          target: '.tour-spares',
          content: 'Check the Spares & Facilities tab to verify component availability and depot capacity before scheduling maintenance.',
          placement: 'bottom',
        }
      ];
    } else if (userRole === 'SYS_ADMIN') {
      roleSteps = [
        {
          target: '.tour-security',
          content: 'The Audit & Security dashboard provides a real-time look at cryptographic integrity and air-gapped egress isolation.',
          placement: 'bottom',
        }
      ];
    } else {
      roleSteps = [
        {
          target: '.tour-fleet-overview',
          content: 'Monitor fleet health and analytics from this main dashboard.',
          placement: 'bottom',
        }
      ];
    }

    setSteps([...commonSteps, ...roleSteps]);
  }, [userRole]);

  const handleJoyrideCallback = (data: CallBackProps) => {
    const { status } = data;
    const finishedStatuses: string[] = [STATUS.FINISHED, STATUS.SKIPPED];

    if (finishedStatuses.includes(status)) {
      setRun(false);
      localStorage.setItem(`aeris_tour_completed_${userRole}`, 'true');
    }
  };

  return (
    <Joyride
      steps={steps}
      run={run}
      continuous={true}
      showSkipButton={true}
      showProgress={true}
      callback={handleJoyrideCallback}
      styles={{
        options: {
          primaryColor: '#3b82f6', // var(--color-primary)
          backgroundColor: '#0f172a', // var(--color-bg-panel)
          textColor: '#e2e8f0', // var(--color-text-primary)
          arrowColor: '#0f172a',
        },
        tooltipContainer: {
          textAlign: 'left',
        },
        buttonNext: {
          backgroundColor: '#3b82f6',
        },
        buttonBack: {
          color: '#94a3b8', // var(--color-text-muted)
        }
      }}
    />
  );
};
