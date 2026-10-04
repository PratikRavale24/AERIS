import React from 'react';
import { Package, Building2, AlertTriangle, Clock, CheckCircle2 } from 'lucide-react';

interface SpareItem {
  part_no: string; description?: string; stock: number; min_stock: number;
  lead_time_days: number; criticality: string; facility_id?: string; status: string;
  affected_components?: Array<{ component_id: string; aircraft_id: string }>;
}

interface FacilityItem {
  facility_id: string; name: string; capability: string;
  slots_available: number; avg_turnaround_days: number;
}

interface SparesFacilitiesViewProps {
  spares: SpareItem[];
  facilities: FacilityItem[];
  readinessData?: any[];
}

const ReadinessBadge: React.FC<{status: string}> = ({status}) => {
  const s = status.toUpperCase();
  const c = s === 'SHORTAGE' ? {color: 'var(--color-critical-text)', bg: 'var(--color-critical)', icon: <AlertTriangle className="w-3 h-3" />}
    : s === 'LOW_STOCK' ? {color: 'var(--color-caution-text)', bg: 'var(--color-caution)', icon: <Clock className="w-3 h-3" />}
    : {color: 'var(--color-ok-text)', bg: 'var(--color-ok)', icon: <CheckCircle2 className="w-3 h-3" />};
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold"
          style={{ backgroundColor: c.bg + '20', color: c.color, border: `1px solid ${c.bg}40` }}>
      {c.icon} {s === 'LOW_STOCK' ? 'LIMITED' : s === 'SHORTAGE' ? 'SHORTAGE' : 'READY'}
    </span>
  );
};

export const SparesFacilitiesView: React.FC<SparesFacilitiesViewProps> = ({ spares, facilities, readinessData = [] }) => {
  const shortages = spares.filter(s => s.status === 'SHORTAGE' || s.status === 'LOW_STOCK').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-panel p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
           style={{ backgroundColor: 'var(--color-bg-panel)', border: '1px solid var(--color-border)' }}>
        <div>
          <h2 className="text-section flex items-center gap-2" style={{ color: 'var(--color-text-primary)' }}>
            <Package className="w-5 h-5" style={{ color: 'var(--color-primary)' }} />
            Spare Readiness & Facility Capacity
          </h2>
          <p className="text-[12px] mt-1" style={{ color: 'var(--color-text-muted)' }}>
            Lead-time vs RUL analysis · Hangar bay utilization
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded text-[11px] font-medium"
                style={{ backgroundColor: 'var(--color-bg-inset)', color: 'var(--color-text-secondary)', border: '1px solid var(--color-border-subtle)' }}>
            {spares.length} Spares Tracked
          </span>
          <span className="px-2.5 py-1 rounded text-[11px] font-medium"
                style={{ backgroundColor: 'var(--color-bg-inset)', color: 'var(--color-text-secondary)', border: '1px solid var(--color-border-subtle)' }}>
            {facilities.length} Facilities
          </span>
          {shortages > 0 && (
            <span className="px-2.5 py-1 rounded text-[11px] font-semibold"
                  style={{ backgroundColor: 'var(--color-critical)20', color: 'var(--color-critical-text)', border: '1px solid var(--color-critical)40' }}>
              <AlertTriangle className="w-3 h-3 inline mr-1" />{shortages} Shortage{shortages > 1 ? 's' : ''}
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Spares Table */}
        <div className="lg:col-span-7 tour-spares-table">
          <div className="rounded-panel overflow-hidden"
               style={{ backgroundColor: 'var(--color-bg-panel)', border: '1px solid var(--color-border)' }}>
            <div className="px-4 py-3" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
              <h3 className="text-[12px] font-semibold uppercase tracking-wider flex items-center gap-2"
                  style={{ color: 'var(--color-text-muted)' }}>
                <Package className="w-3.5 h-3.5" /> Spares Inventory
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-[13px]">
                <thead>
                  <tr style={{ backgroundColor: 'var(--color-bg-raised)' }}>
                    {['Part Number', 'Criticality', 'Stock / Min', 'Lead Time', 'Readiness'].map(h => (
                      <th key={h} className="px-4 py-2.5 font-semibold text-[11px] uppercase tracking-wider"
                          style={{ color: 'var(--color-text-muted)', borderBottom: '1px solid var(--color-border-subtle)' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {spares.map((item) => (
                    <tr key={item.part_no} style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                      <td className="px-4 py-3">
                        <div className="font-semibold" style={{ color: 'var(--color-text-primary)' }}>{item.part_no}</div>
                        <div className="text-[11px]" style={{ color: 'var(--color-text-muted)' }}>{item.description || 'Aircraft Critical Part'}</div>
                      </td>
                      <td className="px-4 py-3 text-[12px] font-semibold" style={{ color: 'var(--color-text-secondary)' }}>
                        {item.criticality}
                      </td>
                      <td className="px-4 py-3 tabular-nums">
                        <span className="font-semibold" style={{ color: (item.status === 'SHORTAGE' || item.status === 'LOW_STOCK') ? 'var(--color-critical-text)' : 'var(--color-ok-text)' }}>
                          {item.stock}
                        </span>
                        <span className="text-[11px]" style={{ color: 'var(--color-text-muted)' }}> / min {item.min_stock}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="font-semibold tabular-nums" style={{ color: 'var(--color-caution-text)' }}>
                          {item.lead_time_days}
                        </span>
                        <span className="text-[11px]" style={{ color: 'var(--color-text-muted)' }}> days</span>
                      </td>
                      <td className="px-4 py-3"><ReadinessBadge status={item.status} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Facilities */}
        <div className="lg:col-span-5 space-y-3 tour-facility-cards">
          <h3 className="text-[12px] font-semibold uppercase tracking-wider flex items-center gap-2 px-1"
              style={{ color: 'var(--color-text-muted)' }}>
            <Building2 className="w-3.5 h-3.5" /> Facility Capacity
          </h3>
          {facilities.map((fac) => {
            const caps = (fac.capability || '').split(',').map(c => c.trim()).filter(Boolean);
            return (
              <div key={fac.facility_id} className="rounded-panel p-4"
                   style={{ backgroundColor: 'var(--color-bg-panel)', border: '1px solid var(--color-border)' }}>
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="font-semibold" style={{ color: 'var(--color-text-primary)' }}>{fac.name}</h4>
                    <p className="text-[11px] mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
                      {fac.facility_id} · Avg turnaround: {fac.avg_turnaround_days} days
                    </p>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[11px] font-bold"
                        style={{
                          backgroundColor: fac.slots_available > 0 ? 'var(--color-ok)20' : 'var(--color-critical)20',
                          color: fac.slots_available > 0 ? 'var(--color-ok-text)' : 'var(--color-critical-text)',
                          border: `1px solid ${fac.slots_available > 0 ? 'var(--color-ok)' : 'var(--color-critical)'}40`,
                        }}>
                    {fac.slots_available} Slot{fac.slots_available !== 1 ? 's' : ''} Available
                  </span>
                </div>
                {caps.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {caps.map(cap => (
                      <span key={cap} className="px-2 py-0.5 rounded text-[10px] font-medium"
                            style={{ backgroundColor: 'var(--color-bg-inset)', color: 'var(--color-text-muted)', border: '1px solid var(--color-border-subtle)' }}>
                        {cap}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
