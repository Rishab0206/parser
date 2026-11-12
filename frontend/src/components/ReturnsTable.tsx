import React, { useState } from 'react';
import { ReturnRecord } from '../api/returns';
import { formatCurrency, formatDate } from '../utils/format';
import { AlertTriangle, CheckCircle2, XCircle, Info, X } from 'lucide-react';

interface ReturnsTableProps {
  returns: ReturnRecord[];
}

export const ReturnsTable: React.FC<ReturnsTableProps> = ({ returns }) => {
  const [selectedReturn, setSelectedReturn] = useState<ReturnRecord | null>(null);

  if (!returns || returns.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-500 text-sm">
        No return / bounce transactions detected. All mandate presentations honored.
      </div>
    );
  }

  return (
    <>
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="p-3.5 bg-rose-50/70 border-b border-rose-100 flex items-center gap-2 text-xs text-rose-800">
          <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
          <span>
            <strong>Return Reconciliation:</strong> Bounce charges (penalties) are isolated into a separate column and never merged into return credit.
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-medium">
              <tr>
                <th className="py-3 px-4">Original EMI Date</th>
                <th className="py-3 px-4">Lender / Counterparty</th>
                <th className="py-3 px-4">EMI Amount</th>
                <th className="py-3 px-4">Return Date</th>
                <th className="py-3 px-4">Return Reversal</th>
                <th className="py-3 px-4">Bounce Charge (Fee)</th>
                <th className="py-3 px-4">Reason</th>
                <th className="py-3 px-4">Recovery Status</th>
                <th className="py-3 px-4">Source</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {returns.map((r) => (
                <tr
                  key={r.id}
                  onClick={() => setSelectedReturn(r)}
                  className="hover:bg-slate-50 cursor-pointer transition-colors"
                >
                  <td className="py-3 px-4 text-slate-700 whitespace-nowrap">{formatDate(r.original_emi_date)}</td>
                  <td className="py-3 px-4 font-semibold text-slate-900">{r.lender_name}</td>
                  <td className="py-3 px-4 font-medium text-slate-700">{formatCurrency(r.emi_amount)}</td>
                  <td className="py-3 px-4 text-rose-700 font-medium whitespace-nowrap">{formatDate(r.return_date)}</td>
                  <td className="py-3 px-4 font-bold text-slate-900">{formatCurrency(r.return_amount)}</td>
                  <td className="py-3 px-4 font-semibold text-rose-600">
                    {r.return_charge_amount > 0 ? formatCurrency(r.return_charge_amount) : "—"}
                  </td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-50 text-rose-800 border border-rose-200 uppercase">
                      {r.reason}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                      r.recovery_status === 'RECOVERED'
                        ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                        : 'bg-amber-100 text-amber-800 border border-amber-200'
                    }`}>
                      {r.recovery_status === 'RECOVERED' ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                      {r.recovery_status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-400 whitespace-nowrap">p.{r.source_page_no}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Detail Modal */}
      {selectedReturn && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full p-6 border border-slate-200 animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <h3 className="text-sm font-bold text-slate-800">Return & Bounce Verification</h3>
              <button
                onClick={() => setSelectedReturn(null)}
                className="p-1 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3.5 text-xs">
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 space-y-1.5">
                <span className="text-[11px] text-slate-400 font-medium uppercase block">Original EMI Presentation</span>
                <div className="font-semibold text-slate-900 text-sm">
                  {formatCurrency(selectedReturn.emi_amount)} on {formatDate(selectedReturn.original_emi_date)}
                </div>
                <div className="font-mono text-slate-600 text-[11px] bg-white p-2 rounded border border-slate-200 break-all">
                  {selectedReturn.original_txn_narration || "No original narration found"}
                </div>
              </div>

              <div className="bg-rose-50/50 p-3 rounded-lg border border-rose-200 space-y-1.5">
                <span className="text-[11px] text-rose-500 font-medium uppercase block">Return Reversal Credit</span>
                <div className="font-semibold text-rose-900 text-sm">
                  {formatCurrency(selectedReturn.return_amount)} on {formatDate(selectedReturn.return_date)}
                </div>
                <div className="font-mono text-rose-800 text-[11px] bg-white p-2 rounded border border-rose-200 break-all">
                  {selectedReturn.return_txn_narration || "No return narration found"}
                </div>
              </div>

              {selectedReturn.return_charge_amount > 0 && (
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 flex justify-between items-center">
                  <span className="text-slate-600">Separate Bank Bounce Charge:</span>
                  <span className="font-bold text-rose-600">{formatCurrency(selectedReturn.return_charge_amount)}</span>
                </div>
              )}

              <div className="flex justify-between items-center pt-2 text-slate-500 border-t border-slate-100">
                <span>Verified on Source Page {selectedReturn.source_page_no}</span>
                <span className="font-medium text-slate-700">{selectedReturn.recovery_status}</span>
              </div>
            </div>

            <div className="mt-5 pt-3 border-t border-slate-100 flex justify-end">
              <button
                onClick={() => setSelectedReturn(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white font-medium rounded-lg text-xs"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

