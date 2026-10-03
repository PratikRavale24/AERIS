import React, { useState } from 'react';
import { 
  Plane, AlertTriangle, CheckCircle2, Search, Filter, ChevronRight, 
  Wrench, TrendingDown, Download
} from 'lucide-react';

interface AircraftSummary {
  id: string; tail_number: string; fleet_type: string; base_location: string;
  status: string; flight_hours: number; highest_risk: number; min_rul: number;
  high_risk_components: number; next_maintenance?: string;
}

interface FleetOverviewProps {
  summary: {
    total_aircraft: number; readiness_rate: number; high_risk_count: number;
    pending_recommendations: number; spares_bottlenecks: number;
    status_counts: Record<string, number>;
  } | null;
  aircraftList: AircraftSummary[];
  onSelectAircraft: (id: string) => void;
}

// Reusable KPI Tile
const KpiTile: React.FC<{label: string; value: string | number; sub?: string; statusColor?: string; icon: React.ReactNode}> = 
  ({label, value, sub, statusColor, icon}) => (
  <div className="rounded-panel p-4 flex items-start justify-between transition-all duration-300 hover:-translate-y-1 hover:shadow-lg"
       style={{ backgroundColor: 'var(--color-bg-panel)', border: '1px solid var(--color-border)', boxShadow: 'var(--shadow-sm)' }}>
    <div className="flex-1 min-w-0">
      <p className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: 'var(--color-text-muted)' }}>{label}</p>
      <p className="text-metric mt-1 tracking-tight" style={{ color: statusColor || 'var(--color-text-primary)' }}>{value}</p>
      {sub && <p className="text-[11px] mt-0.5" style={{ color: 'var(--color-text-muted)' }}>{sub}</p>}
    </div>
    <div className="w-10 h-10 rounded-panel flex items-center justify-center shrink-0 ml-3 transition-colors duration-300"
         style={{ backgroundColor: 'var(--color-bg-inset)', border: '1px solid var(--color-border-subtle)' }}>
      {icon}
    </div>
  </div>
);

// Status Badge
const StatusBadge: React.FC<{status: string}> = ({status}) => {
  const styles: Record<string, {bg: string; text: string; border: string}> = {
    FMC: {bg: 'var(--color-ok)', text: '#fff', border: 'var(--color-ok)'},
    PMC: {bg: 'var(--color-caution)', text: '#fff', border: 'var(--color-caution)'},
    NMC: {bg: 'var(--color-critical)', text: '#fff', border: 'var(--color-critical)'},
  };
  const s = styles[status] || styles.FMC;
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase"
          style={{ backgroundColor: s.bg + '20', color: s.text === '#fff' ? (status === 'FMC' ? 'var(--color-ok-text)' : status === 'PMC' ? 'var(--color-caution-text)' : 'var(--color-critical-text)') : s.text, border: `1px solid ${s.border}40` }}>
      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: s.bg }} />
      {status}
    </span>
  );
};

// Risk Level helpers
const getRiskTier = (risk: number) => {
  if (risk >= 0.7) return { label: 'HIGH', color: 'var(--color-critical-text)', bg: 'var(--color-critical)' };
  if (risk >= 0.3) return { label: 'MEDIUM', color: 'var(--color-caution-text)', bg: 'var(--color-caution)' };
  return { label: 'LOW', color: 'var(--color-ok-text)', bg: 'var(--color-ok)' };
};

export const FleetOverview: React.FC<FleetOverviewProps> = ({ summary, aircraftList, onSelectAircraft }) => {
  const [search, setSearch] = useState('');
  const [fleetFilter, setFleetFilter] = useState('ALL');
  const [riskFilter, setRiskFilter] = useState('ALL');

  const filteredAircraft = aircraftList.filter((ac) => {
    const matchesSearch =
      ac.tail_number.toLowerCase().includes(search.toLowerCase()) ||
      ac.fleet_type.toLowerCase().includes(search.toLowerCase()) ||
      ac.base_location.toLowerCase().includes(search.toLowerCase());
    const matchesFleet = fleetFilter === 'ALL' || ac.fleet_type === fleetFilter;
    let matchesRisk = true;
    if (riskFilter === 'HIGH') matchesRisk = ac.highest_risk >= 0.7;
    else if (riskFilter === 'MEDIUM') matchesRisk = ac.highest_risk >= 0.3 && ac.highest_risk < 0.7;
    else if (riskFilter === 'LOW') matchesRisk = ac.highest_risk < 0.3;
    return matchesSearch && matchesFleet && matchesRisk;
  });

  const handleExportCsv = () => {
    const headers = ['Tail Number', 'Fleet Type', 'Base Location', 'Status', 'Flight Hours', 'Highest Risk', 'Est Min RUL'];
    const rows = filteredAircraft.map(ac => [
      ac.tail_number, ac.fleet_type, ac.base_location, ac.status,
      ac.flight_hours, `${(ac.highest_risk * 100).toFixed(1)}%`, ac.min_rul
    ]);
    const csvContent = [headers, ...rows].map(e => e.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `AERIS_Fleet_Summary_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* KPI Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <KpiTile label="Total Aircraft" value={summary?.total_aircraft ?? 0} sub="Monitored assets"
                 icon={<Plane className="w-5 h-5" style={{ color: 'var(--color-primary)' }} />} />
        <KpiTile label="Fleet Availability" value={summary ? `${(summary.readiness_rate * 100).toFixed(1)}%` : '—'}
                 sub="FMC + PMC" statusColor="var(--color-ok-text)"
                 icon={<CheckCircle2 className="w-5 h-5" style={{ color: 'var(--color-ok-text)' }} />} />
        <KpiTile label="High Risk Assets" value={summary?.high_risk_count ?? 0} sub="Risk ≥ 70%"
                 statusColor="var(--color-critical-text)"
                 icon={<AlertTriangle className="w-5 h-5" style={{ color: 'var(--color-critical-text)' }} />} />
        <KpiTile label="Pending Actions" value={summary?.pending_recommendations ?? 0} sub="Decision queue"
                 statusColor="var(--color-caution-text)"
                 icon={<Wrench className="w-5 h-5" style={{ color: 'var(--color-caution-text)' }} />} />
        <KpiTile label="Spare Shortages" value={summary?.spares_bottlenecks ?? 0} sub="Lead time > RUL"
                 icon={<TrendingDown className="w-5 h-5" style={{ color: 'var(--color-text-muted)' }} />} />
      </div>

      {/* Filters */}
      <div className="rounded-panel p-4 flex flex-col md:flex-row gap-4 items-center justify-between"
           style={{ backgroundColor: 'var(--color-bg-panel)', border: '1px solid var(--color-border)' }}>
        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-text-muted)' }} />
          <input type="text" placeholder="Search tail number, type, base..." value={search}
                 onChange={(e) => setSearch(e.target.value)}
                 className="w-full pl-9 pr-4 py-2 rounded-panel text-[13px] outline-none"
                 style={{ backgroundColor: 'var(--color-bg-inset)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)' }} />
        </div>
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4" style={{ color: 'var(--color-text-muted)' }} />
            <select value={fleetFilter} onChange={(e) => setFleetFilter(e.target.value)}
                    className="rounded-panel px-3 py-1.5 text-[12px] outline-none"
                    style={{ backgroundColor: 'var(--color-bg-inset)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)' }}>
              <option value="ALL">All Types</option>
              <option value="Su-30MKI">Su-30MKI</option>
              <option value="Rafale">Rafale</option>
              <option value="Tejas MK1A">Tejas MK1A</option>
              <option value="C-130J">C-130J</option>
              <option value="AH-64E">AH-64E</option>
              <option value="Mirage 2000">Mirage 2000</option>
            </select>
          </div>
          <select value={riskFilter} onChange={(e) => setRiskFilter(e.target.value)}
                  className="rounded-panel px-3 py-1.5 text-[12px] outline-none"
                  style={{ backgroundColor: 'var(--color-bg-inset)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)' }}>
            <option value="ALL">All Risk</option>
            <option value="HIGH">High (≥70%)</option>
            <option value="MEDIUM">Medium (30-69%)</option>
            <option value="LOW">Low (&lt;30%)</option>
          </select>
          <button onClick={handleExportCsv}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-panel text-[12px] font-medium text-white"
                  style={{ backgroundColor: 'var(--color-primary-strong)' }}>
            <Download className="w-3.5 h-3.5" /> Export CSV
          </button>
        </div>
      </div>

      {/* Priority Queue Table */}
      <div className="rounded-panel overflow-hidden"
           style={{ backgroundColor: 'var(--color-bg-panel)', border: '1px solid var(--color-border)' }}>
        <div className="px-4 py-3 flex items-center justify-between"
             style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
          <h3 className="text-[13px] font-semibold uppercase tracking-wider" style={{ color: 'var(--color-text-secondary)' }}>
            Fleet Asset Register — {filteredAircraft.length} Aircraft
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[13px]">
            <thead>
              <tr style={{ backgroundColor: 'var(--color-bg-raised)', borderBottom: '1px solid var(--color-border-subtle)' }}>
                <th className="px-4 py-2.5 font-semibold text-[11px] uppercase tracking-wider" style={{ color: 'var(--color-text-muted)' }}>Aircraft</th>
                <th className="px-4 py-2.5 font-semibold text-[11px] uppercase tracking-wider" style={{ color: 'var(--color-text-muted)' }}>Platform</th>
                <th className="px-4 py-2.5 font-semibold text-[11px] uppercase tracking-wider" style={{ color: 'var(--color-text-muted)' }}>Base</th>
                <th className="px-4 py-2.5 font-semibold text-[11px] uppercase tracking-wider" style={{ color: 'var(--color-text-muted)' }}>Status</th>
                <th className="px-4 py-2.5 font-semibold text-[11px] uppercase tracking-wider text-right" style={{ color: 'var(--color-text-muted)' }}>Failure Risk</th>
                <th className="px-4 py-2.5 font-semibold text-[11px] uppercase tracking-wider text-right" style={{ color: 'var(--color-text-muted)' }}>Est. RUL</th>
                <th className="px-4 py-2.5 font-semibold text-[11px] uppercase tracking-wider text-right" style={{ color: 'var(--color-text-muted)' }}>Flight Hrs</th>
                <th className="px-4 py-2.5" />
              </tr>
            </thead>
            <tbody>
              {filteredAircraft.map((ac) => {
                const tier = getRiskTier(ac.highest_risk);
                return (
                  <tr key={ac.id} onClick={() => onSelectAircraft(ac.id)}
                      className="cursor-pointer group transition-colors duration-200 hover:bg-[var(--color-bg-hover)]"
                      style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                    <td className="px-4 py-3">
                      <span className="font-bold tracking-wide" style={{ color: 'var(--color-text-primary)' }}>{ac.tail_number}</span>
                    </td>
                    <td className="px-4 py-3 font-medium" style={{ color: 'var(--color-text-secondary)' }}>{ac.fleet_type}</td>
                    <td className="px-4 py-3" style={{ color: 'var(--color-text-secondary)' }}>{ac.base_location}</td>
                    <td className="px-4 py-3"><StatusBadge status={ac.status} /></td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <div className="w-16 h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--color-bg-inset)' }}>
                          <div className={`h-full rounded-full transition-all duration-700 ${tier.label === 'HIGH' ? 'animate-pulse' : ''}`} style={{ width: `${Math.max(5, ac.highest_risk * 100)}%`, backgroundColor: tier.bg, boxShadow: `0 0 8px ${tier.bg}60` }} />
                        </div>
                        <span className="text-[12px] font-bold tabular-nums w-10 text-right" style={{ color: tier.color }}>
                          {(ac.highest_risk * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="text-[13px] font-semibold tabular-nums" style={{ color: 'var(--color-text-primary)' }}>
                        {ac.min_rul}
                      </span>
                      <span className="text-[11px] ml-1" style={{ color: 'var(--color-text-muted)' }}>cyc</span>
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums" style={{ color: 'var(--color-text-secondary)' }}>
                      {ac.flight_hours.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <ChevronRight className="w-4 h-4 opacity-40 group-hover:opacity-100" style={{ color: 'var(--color-primary)' }} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {filteredAircraft.length === 0 && (
        <div className="rounded-panel p-12 text-center"
             style={{ backgroundColor: 'var(--color-bg-panel)', border: '1px solid var(--color-border)' }}>
          <Plane className="w-10 h-10 mx-auto mb-3" style={{ color: 'var(--color-text-muted)' }} />
          <h3 className="text-[15px] font-semibold" style={{ color: 'var(--color-text-primary)' }}>No aircraft found</h3>
          <p className="text-[13px] mt-1" style={{ color: 'var(--color-text-muted)' }}>
            Adjust search or filter criteria to view fleet assets.
          </p>
        </div>
      )}
    </div>
  );
};
