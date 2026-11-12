import React, { useState } from 'react';
import { EmiRecord, EmiDetail, getEmiDetail } from '../api/emi';
import { formatCurrency, formatDate } from '../utils/format';
import { EmiDetailDrawer } from './EmiDetailDrawer';
import { ChevronRight, ShieldCheck, AlertCircle } from 'lucide-react';

interface EmiTableProps {
  emis: EmiRecord[];
  applicationId: string;
}

export const EmiTable: React.FC<EmiTableProps> = ({ emis, applicationId }) => {
  const [selectedDetail, setSelectedDetail] = useState<EmiDetail | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const handleRowClick = async (emi: EmiRecord) => {
    try {
      setLoadingId(emi.id);
      const detail = await getEmiDetail(applicationId, emi.id);
      setSelectedDetail(detail);
      setIsDrawerOpen(true);
    } catch (e) {
      console.error("Failed to load EMI details", e);
    } finally {
      setLoadingId(null);
    }
  };

  if (!emis || emis.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-500 text-sm">
        No recurring loan EMIs detected in the uploaded statements.
      </div>
    );
  }

  return (
    <>
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-medium">
              <tr>
                <th className="py-3 px-4">Latest Date</th>
                <th className="py-3 px-4">Bank & Account</th>
                <th className="py-3 px-4">Lender</th>
                <th className="py-3 px-4">Amount</th>
                <th className="py-3 px-4">Mode</th>
                <th className="py-3 px-4">Frequency</th>
                <th className="py-3 px-4">Attempts</th>
                <th className="py-3 px-4">Confidence</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {emis.map((emi) => (
                <tr
                  key={emi.id}
                  onClick={() => handleRowClick(emi)}
                  className="hover:bg-blue-50/50 cursor-pointer transition-colors group"
                >
                  <td className="py-3 px-4 text-slate-700 whitespace-nowrap">{formatDate(emi.latest_date || emi.last_date)}</td>
                  <td className="py-3 px-4 whitespace-nowrap">
                    <span className="font-semibold text-slate-800 block">{emi.bank_name}</span>
                    <span className="text-[11px] font-mono text-slate-400">{emi.masked_account}</span>
                  </td>
                  <td className="py-3 px-4 font-semibold text-slate-900">{emi.lender_name || "—"}</td>
                  <td className="py-3 px-4 font-bold text-slate-900">{formatCurrency(emi.amount)}</td>
                  <td className="py-3 px-4 text-slate-600 font-mono text-[11px]">{emi.latest_mode}</td>
                  <td className="py-3 px-4 text-slate-600">{emi.frequency}</td>
                  <td className="py-3 px-4 text-slate-600">
                    <span className="font-semibold text-slate-800">{emi.total_attempts}</span>
                    <span className="text-[11px] text-slate-400 ml-1">({emi.total_success} ok, {emi.total_returns} ret)</span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${
                      emi.lender_confidence === 'CONFIRMED'
                        ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                        : emi.lender_confidence === 'PROBABLE'
                        ? 'bg-blue-100 text-blue-800 border border-blue-200'
                        : 'bg-amber-100 text-amber-800 border border-amber-200'
                    }`}>
                      {emi.lender_confidence === 'CONFIRMED' ? <ShieldCheck className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
                      {emi.lender_confidence}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium ${
                      emi.total_returns > 0 ? 'bg-rose-50 text-rose-700 border border-rose-200' : 'bg-slate-100 text-slate-700'
                    }`}>
                      {emi.total_returns > 0 ? `${emi.total_returns} Bounces` : 'Active'}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <span className="inline-flex items-center gap-1 text-blue-600 font-medium text-xs group-hover:translate-x-0.5 transition-transform">
                      {loadingId === emi.id ? 'Loading...' : 'Details'}
                      <ChevronRight className="w-4 h-4" />
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <EmiDetailDrawer
        detail={selectedDetail}
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
      />
    </>
  );
};

