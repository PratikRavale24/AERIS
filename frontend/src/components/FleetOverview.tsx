import React, { useState } from 'react';
import { 
  Plane, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  Search, 
  Filter, 
  ChevronRight, 
  Wrench,
  Gauge,
  TrendingDown,
  ShieldAlert
} from 'lucide-react';

interface AircraftSummary {
  id: string;
  tail_number: string;
  fleet_type: string;
  base_location: string;
  status: string;
  flight_hours: number;
  highest_risk: number;
  min_rul: number;
  high_risk_components: number;
  next_maintenance?: string;
}

interface FleetOverviewProps {
  summary: {
    total_aircraft: number;
    readiness_rate: number;
    high_risk_count: number;
    pending_recommendations: number;
    spares_bottlenecks: number;
    status_counts: Record<string, number>;
  } | null;
  aircraftList: AircraftSummary[];
  onSelectAircraft: (id: string) => void;
}

export const FleetOverview: React.FC<FleetOverviewProps> = ({
  summary,
  aircraftList,
  onSelectAircraft,
}) => {
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

  return (
    <div className="space-y-6">
      {/* ── Top KPI Bar ────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* KPI 1: Fleet Count */}
        <div className="bg-[#111827] border border-gray-800 rounded-xl p-4 flex items-center justify-between shadow-lg">
          <div>
            <p className="text-xs font-mono text-gray-400 uppercase">Total Fleet Size</p>
            <p className="text-3xl font-extrabold text-white mt-1">{summary?.total_aircraft ?? 0}</p>
            <p className="text-xs text-gray-400 mt-1 font-mono">Monitored Assets</p>
          </div>
          <div className="w-12 h-12 rounded-lg bg-blue-950/80 border border-blue-800/60 flex items-center justify-center text-blue-400">
            <Plane className="w-6 h-6" />
          </div>
        </div>

        {/* KPI 2: Readiness Rate */}
        <div className="bg-[#111827] border border-gray-800 rounded-xl p-4 flex items-center justify-between shadow-lg">
          <div>
            <p className="text-xs font-mono text-gray-400 uppercase">Fleet Readiness</p>
            <p className="text-3xl font-extrabold text-emerald-400 mt-1">
              {summary ? `${(summary.readiness_rate * 100).toFixed(1)}%` : '0%'}
            </p>
            <p className="text-xs text-emerald-500/80 mt-1 font-mono">FMC + PMC Ratio</p>
          </div>
          <div className="w-12 h-12 rounded-lg bg-emerald-950/80 border border-emerald-800/60 flex items-center justify-center text-emerald-400">
            <CheckCircle2 className="w-6 h-6" />
          </div>
        </div>

        {/* KPI 3: High Risk Aircraft */}
        <div className="bg-[#111827] border border-gray-800 rounded-xl p-4 flex items-center justify-between shadow-lg">
          <div>
            <p className="text-xs font-mono text-gray-400 uppercase">High Degradation Risk</p>
            <p className="text-3xl font-extrabold text-red-400 mt-1">{summary?.high_risk_count ?? 0}</p>
            <p className="text-xs text-red-400/80 mt-1 font-mono">Risk Probability &gt; 70%</p>
          </div>
          <div className="w-12 h-12 rounded-lg bg-red-950/80 border border-red-800/60 flex items-center justify-center text-red-400">
            <AlertTriangle className="w-6 h-6" />
          </div>
        </div>

        {/* KPI 4: Pending Recommendations */}
        <div className="bg-[#111827] border border-gray-800 rounded-xl p-4 flex items-center justify-between shadow-lg">
          <div>
            <p className="text-xs font-mono text-gray-400 uppercase">Pending Actions</p>
            <p className="text-3xl font-extrabold text-amber-400 mt-1">{summary?.pending_recommendations ?? 0}</p>
            <p className="text-xs text-amber-400/80 mt-1 font-mono">Decision Support Queue</p>
          </div>
          <div className="w-12 h-12 rounded-lg bg-amber-950/80 border border-amber-800/60 flex items-center justify-center text-amber-400">
            <Wrench className="w-6 h-6" />
          </div>
        </div>

        {/* KPI 5: Supply Bottlenecks */}
        <div className="bg-[#111827] border border-gray-800 rounded-xl p-4 flex items-center justify-between shadow-lg">
          <div>
            <p className="text-xs font-mono text-gray-400 uppercase">Supply Bottlenecks</p>
            <p className="text-3xl font-extrabold text-purple-400 mt-1">{summary?.spares_bottlenecks ?? 0}</p>
            <p className="text-xs text-purple-400/80 mt-1 font-mono">Lead Time &gt; RUL</p>
          </div>
          <div className="w-12 h-12 rounded-lg bg-purple-950/80 border border-purple-800/60 flex items-center justify-center text-purple-400">
            <TrendingDown className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* ── Filters & Search Controls ────────────────────────── */}
      <div className="bg-[#111827] border border-gray-800 rounded-xl p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
        {/* Search */}
        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search Tail Number, Type, Base..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded-lg pl-9 pr-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Filter Dropdowns */}
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <span className="text-xs font-mono text-gray-400">Fleet:</span>
            <select
              value={fleetFilter}
              onChange={(e) => setFleetFilter(e.target.value)}
              className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
            >
              <option value="ALL">All Aircraft Types</option>
              <option value="Su-30MKI">Su-30MKI</option>
              <option value="Rafale">Rafale</option>
              <option value="Tejas MK1A">Tejas MK1A</option>
              <option value="C-130J">C-130J Super Hercules</option>
              <option value="AH-64E">AH-64E Apache</option>
              <option value="Mirage 2000">Mirage 2000</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-gray-400">Risk Tier:</span>
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
            >
              <option value="ALL">All Risk Levels</option>
              <option value="HIGH">High Risk (&ge; 70%)</option>
              <option value="MEDIUM">Medium Risk (30–69%)</option>
              <option value="LOW">Low Risk (&lt; 30%)</option>
            </select>
          </div>
        </div>
      </div>

      {/* ── Aircraft Grid ────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredAircraft.map((ac) => {
          const isHighRisk = ac.highest_risk >= 0.7;
          const isMediumRisk = ac.highest_risk >= 0.3 && ac.highest_risk < 0.7;

          let riskBadgeColor = 'bg-emerald-950/80 text-emerald-400 border-emerald-800';
          if (isHighRisk) riskBadgeColor = 'bg-red-950/80 text-red-400 border-red-800 animate-pulse';
          else if (isMediumRisk) riskBadgeColor = 'bg-amber-950/80 text-amber-400 border-amber-800';

          return (
            <div
              key={ac.id}
              onClick={() => onSelectAircraft(ac.id)}
              className={`bg-[#111827] border rounded-xl p-5 hover:border-blue-500/80 transition-all cursor-pointer shadow-lg group relative overflow-hidden ${
                isHighRisk ? 'border-red-900/60' : 'border-gray-800'
              }`}
            >
              {/* Background Risk Indicator Accent */}
              {isHighRisk && (
                <div className="absolute top-0 right-0 w-24 h-24 bg-red-600/10 rounded-full blur-2xl -mr-8 -mt-8" />
              )}

              {/* Header */}
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-lg font-bold text-white group-hover:text-blue-400 transition-colors">
                      {ac.tail_number}
                    </span>
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                      ac.status === 'FMC'
                        ? 'bg-emerald-950 text-emerald-400 border-emerald-800'
                        : ac.status === 'PMC'
                        ? 'bg-amber-950 text-amber-400 border-amber-800'
                        : 'bg-red-950 text-red-400 border-red-800'
                    }`}>
                      {ac.status}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 font-medium mt-0.5">
                    {ac.fleet_type} &bull; <span className="font-mono text-gray-300">{ac.base_location}</span>
                  </p>
                </div>

                <div className={`px-2.5 py-1 rounded-lg border text-xs font-mono font-bold ${riskBadgeColor}`}>
                  {(ac.highest_risk * 100).toFixed(0)}% Risk
                </div>
              </div>

              {/* Component Health & RUL Row */}
              <div className="grid grid-cols-2 gap-3 mt-4 pt-3 border-t border-gray-800/80 text-xs">
                <div>
                  <span className="text-gray-400 block font-mono text-[11px]">Est. Min RUL</span>
                  <span className="text-white font-mono font-semibold text-sm">
                    {ac.min_rul} <span className="text-xs font-normal text-gray-400">cycles</span>
                  </span>
                </div>
                <div>
                  <span className="text-gray-400 block font-mono text-[11px]">Flight Hours</span>
                  <span className="text-white font-mono font-semibold text-sm">
                    {ac.flight_hours.toLocaleString()} <span className="text-xs font-normal text-gray-400">hrs</span>
                  </span>
                </div>
              </div>

              {/* Degradation Progress Bar */}
              <div className="mt-3">
                <div className="flex justify-between text-[11px] font-mono text-gray-400 mb-1">
                  <span>Max Risk Factor</span>
                  <span className={isHighRisk ? 'text-red-400 font-bold' : 'text-gray-300'}>
                    {(ac.highest_risk * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      isHighRisk ? 'bg-red-500' : isMediumRisk ? 'bg-amber-500' : 'bg-emerald-500'
                    }`}
                    style={{ width: `${Math.max(5, ac.highest_risk * 100)}%` }}
                  />
                </div>
              </div>

              {/* Action Footer */}
              <div className="mt-4 pt-3 border-t border-gray-800/60 flex items-center justify-between text-xs text-gray-400 group-hover:text-blue-400 font-medium">
                <span>View Telemetry & RUL Details</span>
                <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          );
        })}
      </div>

      {filteredAircraft.length === 0 && (
        <div className="bg-[#111827] border border-gray-800 rounded-xl p-12 text-center">
          <Plane className="w-12 h-12 text-gray-600 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-white">No aircraft found</h3>
          <p className="text-xs text-gray-400 mt-1">Try adjusting your search query or filter criteria.</p>
        </div>
      )}
    </div>
  );
};
