import React from 'react';
import { 
  Package, 
  Building2, 
  AlertTriangle, 
  TrendingDown, 
  Clock, 
  CheckCircle2, 
  Wrench
} from 'lucide-react';

interface SpareItem {
  part_no: string;
  description?: string;
  stock: number;
  min_stock: number;
  lead_time_days: number;
  criticality: string;
  facility_id?: string;
  status: string;
  affected_components?: Array<{ component_id: string; aircraft_id: string }>;
}

interface FacilityItem {
  facility_id: string;
  name: string;
  capability: string;
  slots_available: number;
  avg_turnaround_days: number;
}

interface SparesFacilitiesViewProps {
  spares: SpareItem[];
  facilities: FacilityItem[];
  readinessData?: any[];
}

export const SparesFacilitiesView: React.FC<SparesFacilitiesViewProps> = ({
  spares,
  facilities,
  readinessData = [],
}) => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between bg-[#111827] border border-gray-800 rounded-xl p-5 shadow-lg">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Package className="w-6 h-6 text-purple-400" /> Supply Chain & Facility Capacity
          </h2>
          <p className="text-xs text-gray-400 font-mono mt-1">
            Spare part lead-time analysis vs component RUL &bull; Hangar bay capacity optimization
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1 bg-purple-950/80 border border-purple-800 text-purple-300 rounded-lg text-xs font-mono">
            {spares.length} Tracked NSN Spares
          </span>
          <span className="px-3 py-1 bg-blue-950/80 border border-blue-800 text-blue-300 rounded-lg text-xs font-mono">
            {facilities.length} Active Maintenance Bases
          </span>
        </div>
      </div>

      {/* Grid: Spares Inventory & Facilities */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Spares Inventory */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-mono uppercase text-gray-400 font-bold flex items-center gap-2">
              <Package className="w-4 h-4 text-purple-400" /> Spares Inventory & Lead Times
            </h3>
          </div>

          <div className="bg-[#111827] border border-gray-800 rounded-xl overflow-hidden shadow-lg">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-gray-900/90 text-gray-400 border-b border-gray-800">
                  <tr>
                    <th className="p-3">Part No & Description</th>
                    <th className="p-3">Criticality</th>
                    <th className="p-3 text-center">Stock / Min</th>
                    <th className="p-3 text-center">Lead Time</th>
                    <th className="p-3 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800/80 text-gray-300">
                  {spares.map((item) => {
                    const isLowStock = item.status === 'SHORTAGE' || item.status === 'LOW_STOCK';

                    return (
                      <tr key={item.part_no} className="hover:bg-gray-800/40 transition-colors">
                        <td className="p-3">
                          <div className="font-bold text-white">{item.part_no}</div>
                          <div className="text-[10px] text-gray-500">{item.description || 'Aircraft Critical Part'}</div>
                        </td>
                        <td className="p-3 text-gray-400 font-bold">{item.criticality}</td>
                        <td className="p-3 text-center">
                          <span className={`font-bold ${isLowStock ? 'text-red-400' : 'text-emerald-400'}`}>
                            {item.stock}
                          </span>
                          <span className="text-gray-500 text-[10px]"> / min {item.min_stock}</span>
                        </td>
                        <td className="p-3 text-center">
                          <span className="text-amber-400 font-bold">{item.lead_time_days} days</span>
                        </td>
                        <td className="p-3 text-right">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            item.status === 'SHORTAGE'
                              ? 'bg-red-950 text-red-400 border border-red-800'
                              : item.status === 'LOW_STOCK'
                              ? 'bg-amber-950 text-amber-400 border border-amber-800'
                              : 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                          }`}>
                            {item.status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right: Facilities Capacity & Maintenance Slots */}
        <div className="lg:col-span-5 space-y-4">
          <h3 className="text-xs font-mono uppercase text-gray-400 font-bold flex items-center gap-2">
            <Building2 className="w-4 h-4 text-blue-400" /> Maintenance Hangar Bay Utilization
          </h3>

          <div className="space-y-3">
            {facilities.map((fac) => {
              const capabilitiesList = (fac.capability || '').split(',').map((c) => c.trim());

              return (
                <div key={fac.facility_id} className="bg-[#111827] border border-gray-800 rounded-xl p-4 shadow-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-bold text-white text-base">{fac.name}</h4>
                      <p className="text-xs text-gray-400 font-mono">ID: {fac.facility_id} &bull; Turnaround: {fac.avg_turnaround_days} days</p>
                    </div>

                    <div className="text-right">
                      <span className={`px-2.5 py-1 rounded text-xs font-mono font-bold ${
                        fac.slots_available > 0 ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-red-950 text-red-400 border border-red-800'
                      }`}>
                        {fac.slots_available} Slots Available
                      </span>
                    </div>
                  </div>

                  {/* Capabilities tags */}
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {capabilitiesList.map((cap) => (
                      <span key={cap} className="px-2 py-0.5 rounded bg-gray-900 text-gray-400 text-[10px] font-mono border border-gray-800">
                        {cap}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
