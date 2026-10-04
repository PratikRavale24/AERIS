import React, { useState, useEffect, useCallback } from 'react';

interface TourStep {
  element: string | null;
  title: string;
  desc: string;
  action: (() => void) | null;
}

interface OnboardingTourProps {
  userRole: string;
  setActiveTab: (tab: string) => void;
  tourTrigger: number; // incremented on each login to re-trigger tour
}

export const OnboardingTour: React.FC<OnboardingTourProps> = ({ userRole, setActiveTab, tourTrigger }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [run, setRun] = useState(false);
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);

  // Trigger tour on every login (tourTrigger changes)
  useEffect(() => {
    if (tourTrigger > 0) {
      setCurrentStep(0);
      setTimeout(() => setRun(true), 600);
    }
  }, [tourTrigger]);

  const buildSteps = useCallback((): TourStep[] => {
    const common: TourStep = {
      element: null,
      title: 'Welcome to AERIS',
      desc: 'Aircraft Engine Reliability Intelligence System — your AI-powered predictive maintenance platform for defense fleet readiness. Let\'s walk through the key features.',
      action: null,
    };

    if (userRole === 'FLEET_SUPERVISOR') {
      return [
        common,
        // Fleet Overview tab
        { element: '.tour-kpi-row', title: 'Fleet KPI Dashboard', desc: 'Total Aircraft: number of monitored assets. Fleet Availability: percentage of FMC + PMC aircraft. High Risk Assets: aircraft with failure probability ≥ 70%. Pending Actions: decisions awaiting your authorization. Spare Shortages: parts where lead time exceeds RUL.', action: () => setActiveTab('fleet') },
        { element: '.tour-fleet-filters', title: 'Search & Filters', desc: 'Search by tail number, platform type, or base location. Filter by fleet type (Su-30MKI, Rafale, Tejas, etc.) and risk level (High/Medium/Low). Export filtered data to CSV for reports.', action: null },
        { element: '.tour-fleet-table', title: 'Fleet Asset Register', desc: 'Each row shows: Tail Number (aircraft ID), Platform type, Base, Status (FMC = Fully Mission Capable, PMC = Partially, NMC = Non-Mission Capable), Failure Risk (AI-predicted probability with progress bar), Est. RUL (Remaining Useful Life in cycles), and Flight Hours. Click any row to open the Digital Twin detail modal.', action: null },
        // Switch to Maintenance Queue
        { element: null, title: 'Maintenance Queue', desc: 'Now let\'s look at the AI-driven Maintenance Queue where you authorize decisions.', action: () => setActiveTab('recommendations') },
        { element: '.tour-rec-list', title: 'Recommendation Cards', desc: 'Each card shows an AI-generated maintenance recommendation sorted by priority. The badge color indicates urgency: CRITICAL (red), HIGH (orange), MEDIUM (yellow). Shows the aircraft ID, component, and recommended action.', action: null },
        { element: '.tour-rec-detail', title: 'Recommendation Detail Panel', desc: 'When you select a recommendation, this panel shows: Priority Score (0–100), Risk Score (failure probability), Estimated RUL range (P10/P50/P90 confidence intervals), Trust Score (AI model confidence), and the Recommended Action.', action: null },
        { element: '.tour-record-decision', title: 'Record Decision', desc: 'This is your decision workspace. Type an operational rationale (minimum 15 characters), then click Accept, Defer, Reject, or Override. The AI recommends — the human decides. Every decision is cryptographically logged to the audit chain.', action: null },
        { element: '.tour-evidence', title: 'Evidence Passport', desc: 'Each recommendation has a SHA-256 evidence passport that cryptographically binds the AI prediction, sensor data, and your decision together. This ensures full traceability and tamper-proof audit compliance.', action: null },
      ];
    }

    if (userRole === 'MAINT_PLANNER') {
      return [
        common,
        // Start on Maintenance Queue (primary tab)
        { element: null, title: 'Maintenance Queue', desc: 'Your primary workspace for reviewing and acting on AI maintenance recommendations.', action: () => setActiveTab('recommendations') },
        { element: '.tour-rec-list', title: 'Priority-Sorted Queue', desc: 'Recommendations are sorted by priority score. CRITICAL items appear first. Each card shows the aircraft, component, and recommended action. Click a card to see full details.', action: null },
        { element: '.tour-rec-detail', title: 'AI Analysis Detail', desc: 'The detail panel shows: Priority Score, Risk Score (failure probability from the ML model), RUL estimates (P10/P50/P90 confidence), Trust Score, and the Recommended Action with reason codes (RUL_CRITICAL, ANOMALY_DETECTED, etc.).', action: null },
        { element: '.tour-record-decision', title: 'Record Your Decision', desc: 'Enter your operational rationale and click Accept, Defer, or Reject. Try it now! Every decision is hash-chained to the audit log. The Override button requires dual-authorization.', action: null },
        { element: '.tour-evidence', title: 'Evidence Passport', desc: 'Cryptographic proof linking AI prediction → sensor data → your decision. SHA-256 hash-chain ensures tamper-proof compliance for Ministry of Defense audits.', action: null },
        // Switch to Spares
        { element: null, title: 'Spare Readiness', desc: 'Let\'s check component availability before scheduling maintenance.', action: () => setActiveTab('spares') },
        { element: '.tour-spares-table', title: 'Spares Inventory', desc: 'Shows Part Number, Criticality level, current Stock vs Minimum required, Lead Time (days for procurement), and Readiness status (READY, LIMITED, SHORTAGE). Red items need immediate procurement action.', action: null },
        { element: '.tour-facility-cards', title: 'Facility Capacity', desc: 'Each card shows a maintenance facility with: name, facility ID, available slots, average turnaround time in days, and the capabilities it supports. Use this to plan scheduling.', action: null },
      ];
    }

    if (userRole === 'MAINT_ENGINEER') {
      return [
        common,
        { element: null, title: 'Maintenance Queue', desc: 'Review AI-generated maintenance recommendations assigned to your role.', action: () => setActiveTab('recommendations') },
        { element: '.tour-rec-list', title: 'Assigned Recommendations', desc: 'Cards sorted by priority. CRITICAL (red) items need immediate attention. Each shows the aircraft, component, and the AI-recommended action.', action: null },
        { element: '.tour-rec-detail', title: 'Detailed Analysis', desc: 'View the AI\'s full analysis: Priority Score, Risk Score (ML failure probability), Remaining Useful Life estimates with confidence intervals, and Trust Score.', action: null },
        { element: '.tour-record-decision', title: 'Record Decision', desc: 'Provide your operational rationale and record your decision. Accept to approve maintenance, Defer to postpone, or Reject with reasoning.', action: null },
        { element: '.tour-evidence', title: 'Evidence Passport', desc: 'SHA-256 hash-chained audit trail. Every recommendation and decision is cryptographically bound for defense-grade traceability.', action: null },
      ];
    }

    if (userRole === 'SPARES_PLANNER') {
      return [
        common,
        { element: null, title: 'Spare Readiness', desc: 'Your primary workspace for managing spare part inventory and facility capacity.', action: () => setActiveTab('spares') },
        { element: '.tour-spares-table', title: 'Spares Inventory Table', desc: 'Part Number: unique identifier. Criticality: CRITICAL/HIGH/MEDIUM/LOW. Stock/Min: current stock vs minimum threshold. Lead Time: procurement duration in days. Readiness: READY (green), LIMITED (yellow), SHORTAGE (red).', action: null },
        { element: '.tour-facility-cards', title: 'Facility Capacity', desc: 'Maintenance facilities with available bay slots, turnaround time, and supported capabilities. Green badge = slots available, red = at capacity.', action: null },
        // Switch to Maintenance Queue for context
        { element: null, title: 'Maintenance Queue', desc: 'Let\'s see the maintenance recommendations that drive spare part demand.', action: () => setActiveTab('recommendations') },
        { element: '.tour-rec-list', title: 'Recommendation Queue', desc: 'These AI recommendations determine which parts are needed. The Part Status column links directly to your inventory — SHORTAGE means procurement is required before maintenance can proceed.', action: null },
      ];
    }

    if (userRole === 'SYS_ADMIN') {
      return [
        common,
        { element: null, title: 'Audit & Security Dashboard', desc: 'Your primary workspace for monitoring system security and cryptographic integrity.', action: () => setActiveTab('security') },
        { element: '.tour-security-posture', title: 'Security Posture Checks', desc: 'Live status of all security controls: TLS 1.2/1.3, Cookie Security Flags (HttpOnly, Secure, SameSite), Content Security Policy, Server-Side RBAC, Audit Chain Hash Integrity, Air-Gapped Egress Isolation, AES-256-GCM Field Encryption, and ML Model HMAC Integrity.', action: null },
        { element: '.tour-audit-chain', title: 'Cryptographic Audit Chain', desc: 'Verifies the SHA-256 hash chain integrity across all maintenance decisions. Shows total entries, verified entries, and chain status. Click "Verify Chain" to run a live integrity check.', action: null },
        { element: '.tour-security-events', title: 'Security Event Log', desc: 'Real-time log of system events: authentication attempts, hash chain verifications, egress probe results, and infrastructure events. Each event shows type, severity, description, and timestamp.', action: null },
        { element: '.tour-data-ingestion', title: 'Data Ingestion', desc: 'Upload and validate sensor data files against the Appendix A Data Contract schema. The system validates file structure, required columns, and data types before ingestion.', action: null },
      ];
    }

    // Default / unknown role
    return [
      common,
      { element: '.tour-kpi-row', title: 'Fleet Dashboard', desc: 'Overview of fleet health metrics including total aircraft, availability rate, high-risk assets, and pending maintenance actions.', action: () => setActiveTab('fleet') },
    ];
  }, [userRole, setActiveTab]);

  const steps = buildSteps();

  const updateRect = useCallback(() => {
    if (!run || currentStep >= steps.length) return;
    const step = steps[currentStep];
    if (step.element) {
      const el = document.querySelector(step.element);
      if (el) {
        const rect = el.getBoundingClientRect();
        setTargetRect(rect);
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        (el as HTMLElement).style.position = 'relative';
        (el as HTMLElement).style.zIndex = '999999';
        (el as HTMLElement).style.pointerEvents = 'auto';
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
    const interval = setInterval(updateRect, 250);
    return () => clearInterval(interval);
  }, [updateRect]);

  const cleanupPrev = useCallback(() => {
    const prevStep = steps[currentStep];
    if (prevStep && prevStep.element) {
      const el = document.querySelector(prevStep.element);
      if (el) {
        (el as HTMLElement).style.position = '';
        (el as HTMLElement).style.zIndex = '';
        (el as HTMLElement).style.pointerEvents = '';
      }
    }
  }, [currentStep, steps]);

  const handleNext = () => {
    cleanupPrev();
    if (currentStep === steps.length - 1) {
      setRun(false);
    } else {
      const nextIdx = currentStep + 1;
      const nextStep = steps[nextIdx];
      if (nextStep.action) {
        nextStep.action();
      }
      setCurrentStep(nextIdx);
    }
  };

  const handlePrev = () => {
    cleanupPrev();
    if (currentStep > 0) {
      const prevIdx = currentStep - 1;
      const prevStep = steps[prevIdx];
      if (prevStep.action) {
        prevStep.action();
      }
      setCurrentStep(prevIdx);
    }
  };

  const handleSkip = () => {
    cleanupPrev();
    setRun(false);
  };

  if (!run || currentStep >= steps.length) return null;

  const step = steps[currentStep];

  // Calculate responsive popover position
  const isMobile = window.innerWidth < 640;
  const popoverWidth = isMobile ? 'calc(100vw - 32px)' : '380px';
  let popoverStyle: React.CSSProperties;

  if (targetRect && !isMobile) {
    // Desktop: position near the element
    let top = targetRect.bottom + 16;
    let left = targetRect.left + (targetRect.width / 2);
    let transform = 'translate(-50%, 0)';

    // Clamp left so popover doesn't go off-screen
    const halfW = 190;
    if (left - halfW < 16) left = halfW + 16;
    if (left + halfW > window.innerWidth - 16) left = window.innerWidth - halfW - 16;

    // If it goes off bottom, place above
    if (targetRect.bottom + 240 > window.innerHeight) {
      top = targetRect.top - 16;
      transform = 'translate(-50%, -100%)';
    }

    popoverStyle = { top: `${top}px`, left: `${left}px`, transform, width: popoverWidth };
  } else if (targetRect && isMobile) {
    // Mobile: fixed at bottom with small offset
    popoverStyle = {
      bottom: '16px', left: '16px', right: '16px', width: 'auto',
      transform: 'none',
    };
  } else {
    // No element: center on screen
    popoverStyle = isMobile
      ? { bottom: '16px', left: '16px', right: '16px', width: 'auto', transform: 'none' }
      : { top: '50%', left: '50%', transform: 'translate(-50%, -50%)', width: popoverWidth };
  }

  return (
    <>
      {/* Overlay with cutout */}
      <div
        style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          zIndex: 999998,
          pointerEvents: targetRect ? 'none' : 'auto',
          background: targetRect ? 'transparent' : 'rgba(0,0,0,0.65)',
          clipPath: targetRect
            ? `polygon(0% 0%, 0% 100%, ${Math.max(0, targetRect.left - 8)}px 100%, ${Math.max(0, targetRect.left - 8)}px ${Math.max(0, targetRect.top - 8)}px, ${Math.min(window.innerWidth, targetRect.right + 8)}px ${Math.max(0, targetRect.top - 8)}px, ${Math.min(window.innerWidth, targetRect.right + 8)}px ${Math.min(window.innerHeight, targetRect.bottom + 8)}px, ${Math.max(0, targetRect.left - 8)}px ${Math.min(window.innerHeight, targetRect.bottom + 8)}px, ${Math.max(0, targetRect.left - 8)}px 100%, 100% 100%, 100% 0%)`
            : 'none',
          transition: 'all 0.3s ease',
        }}
      />

      {/* Popover Card */}
      <div
        className="fixed p-5 rounded-xl shadow-2xl flex flex-col gap-3"
        style={{
          backgroundColor: 'var(--color-bg-panel)',
          border: '1px solid var(--color-border)',
          zIndex: 999999,
          maxHeight: isMobile ? '60vh' : '80vh',
          overflowY: 'auto',
          transition: 'top 0.3s ease, left 0.3s ease, bottom 0.3s ease',
          ...popoverStyle,
        }}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <h3 className="text-base font-bold" style={{ color: 'var(--color-text-primary)' }}>
              {step.title}
            </h3>
          </div>
          <span
            className="text-[11px] font-bold px-2 py-0.5 rounded-full shrink-0"
            style={{ backgroundColor: 'var(--color-primary-strong)', color: '#fff' }}
          >
            {currentStep + 1}/{steps.length}
          </span>
        </div>

        {/* Progress bar */}
        <div className="w-full h-1 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--color-bg-inset)' }}>
          <div
            className="h-full rounded-full transition-all duration-500 ease-out"
            style={{
              width: `${((currentStep + 1) / steps.length) * 100}%`,
              backgroundColor: 'var(--color-primary-strong)',
            }}
          />
        </div>

        {/* Description */}
        <p className="text-[13px] leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
          {step.desc}
        </p>

        {/* Buttons */}
        <div className="flex items-center justify-between gap-2 pt-1">
          <button
            onClick={handleSkip}
            className="text-[12px] font-medium hover:underline transition-colors"
            style={{ color: 'var(--color-text-muted)' }}
          >
            Skip Tour
          </button>

          <div className="flex items-center gap-2">
            {currentStep > 0 && (
              <button
                onClick={handlePrev}
                className="px-3 py-1.5 text-[12px] font-medium rounded-lg transition-colors"
                style={{
                  color: 'var(--color-text-secondary)',
                  backgroundColor: 'var(--color-bg-inset)',
                  border: '1px solid var(--color-border)',
                }}
              >
                Back
              </button>
            )}
            <button
              onClick={handleNext}
              className="px-4 py-1.5 text-[12px] font-semibold text-white rounded-lg transition-transform hover:scale-105 active:scale-95"
              style={{ backgroundColor: 'var(--color-primary-strong)' }}
            >
              {currentStep === steps.length - 1 ? 'Get Started' : 'Next'}
            </button>
          </div>
        </div>
      </div>
    </>
  );
};
