import React from 'react';
import { X, CheckCircle, AlertTriangle, ShieldCheck, FileText, ArrowRight, CornerDownRight } from 'lucide-react';
import { EmiDetail } from '../api/emi';
import { formatCurrency, formatDate } from '../utils/format';

interface EmiDetailDrawerProps {
  detail: EmiDetail | null;
  isOpen: boolean;
  onClose: () => void;
}

export const EmiDetailDrawer: React.FC<EmiDetailDrawerProps> = ({ detail, isOpen, onClose }) => {
  if (!isOpen || !detail) return null;

  const emi = detail.emi_record;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-xl bg-white h-full shadow-2xl flex flex-col animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-800">{emi.lender_name || "—"}</h3>
              <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                emi.lender_confidence === 'CONFIRMED' ? 'bg-emerald-100 text-emerald-800' :
                emi.lender_confidence === 'PROBABLE' ? 'bg-blue-100 text-blue-800' : 'bg-amber-100 text-amber-800'
              }`}>
                {emi.lender_confidence} EMI
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">Loan Repayment Intelligence & Mandate History</p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-200 text-slate-400 hover:text-slate-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {/* Main Key-Value stats */}
          <div className="grid grid-cols-3 gap-3 p-4 bg-slate-50 rounded-xl border border-slate-200">
            <div>
              <span className="text-[11px] text-slate-400 block uppercase font-medium">EMI Amount</span>
              <span className="text-base font-bold text-slate-900">{formatCurrency(emi.amount)}</span>
            </div>
            <div>
              <span className="text-[11px] text-slate-400 block uppercase font-medium">Frequency</span>
              <span className="text-sm font-semibold text-slate-800">{emi.frequency}</span>
            </div>
            <div>
              <span className="text-[11px] text-slate-400 block uppercase font-medium">Bounce Rate</span>
              <span className={`text-sm font-bold ${detail.bounce_rate > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                {detail.bounce_rate.toFixed(1)}%
              </span>
            </div>
          </div>

          {/* Mandate & Account Details */}
          <div className="border border-slate-200 rounded-xl p-4 space-y-2.5 text-xs">
            <h4 className="font-semibold text-slate-800 text-xs flex items-center gap-1.5 border-b border-slate-100 pb-2">
              <ShieldCheck className="w-4 h-4 text-blue-600" />
              Mandate & Source Details
            </h4>
            <div className="grid grid-cols-2 gap-y-2 text-slate-600">
              <div>
                <span className="text-slate-400 block text-[11px]">Mandate Ref / UMRN</span>
                <span className="font-mono text-slate-800">{emi.mandate_ref || "Detected from presentation pattern"}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Debit Bank & Account</span>
                <span className="font-mono text-slate-800">{emi.bank_name} ({emi.masked_account})</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">First Presentation</span>
                <span>{formatDate(emi.first_date)}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Latest Presentation</span>
                <span>{formatDate(emi.last_date)}</span>
              </div>
            </div>
          </div>

          {/* Recovery info if bounce happened */}
          {detail.recovery_info && detail.recovery_info.total_returns > 0 && (
            <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900">
              <h5 className="font-semibold mb-1 flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                Bounce Recovery Status
              </h5>
              <p>
                {detail.recovery_info.recovered_count} of {detail.recovery_info.total_returns} return(s) recovered via re-presentation within 30 days ({detail.recovery_info.recovery_rate_pct}% recovery rate).
              </p>
            </div>
          )}

          {/* All Attempts Table */}
          <div>
            <h4 className="font-semibold text-slate-800 text-xs mb-2.5">
              Presentation History ({detail.attempts.length} attempts: {emi.total_success} success, {emi.total_returns} returned)
            </h4>
            <div className="border border-slate-200 rounded-xl overflow-hidden">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-500">
                  <tr>
                    <th className="py-2 px-3 font-medium">Date</th>
                    <th className="py-2 px-3 font-medium">Amount</th>
                    <th className="py-2 px-3 font-medium">Status</th>
                    <th className="py-2 px-3 font-medium">Page</th>
                    <th className="py-2 px-3 font-medium">Raw Narration</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {detail.attempts.map((att) => (
                    <tr key={att.id} className="hover:bg-slate-50">
                      <td className="py-2 px-3 whitespace-nowrap text-slate-700">{formatDate(att.attempt_date)}</td>
                      <td className="py-2 px-3 font-medium text-slate-900">{formatCurrency(att.amount)}</td>
                      <td className="py-2 px-3 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                          att.status === 'SUCCESS' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
                        }`}>
                          {att.status}
                        </span>
                      </td>
                      <td className="py-2 px-3 text-slate-400">p.{att.source_page_no || 1}</td>
                      <td className="py-2 px-3 text-slate-500 font-mono text-[11px] max-w-xs truncate" title={att.narration_raw}>
                        {att.narration_raw || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between text-xs text-slate-500">
          <span>Source verified against statement raw text</span>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white font-medium rounded-lg"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

