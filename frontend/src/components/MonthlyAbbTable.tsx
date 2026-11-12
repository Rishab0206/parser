import React, { useState } from 'react';
import { MonthlySummary } from '../api/abb';
import { formatCurrency, formatDate, formatPercentage } from '../utils/format';
import { Calendar, TrendingUp, TrendingDown, Info, X } from 'lucide-react';

interface MonthlyAbbTableProps {
  data: MonthlySummary[];
}

export const MonthlyAbbTable: React.FC<MonthlyAbbTableProps> = ({ data }) => {
  const [selectedMonth, setSelectedMonth] = useState<MonthlySummary | null>(null);

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-500 text-sm">
        No monthly ABB data available.
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
                <th className="py-3 px-3.5">Month</th>
                <th className="py-3 px-3.5">Business Turnover</th>
                <th className="py-3 px-3.5">Gross Credit</th>
                <th className="py-3 px-3.5">Total Debit</th>
                <th className="py-3 px-3.5">Net Flow</th>
                <th className="py-3 px-3.5 font-bold text-slate-900">Monthly ABB</th>
                <th className="py-3 px-3.5">Min Balance</th>
                <th className="py-3 px-3.5">Min Date</th>
                <th className="py-3 px-3.5">Month End</th>
                <th className="py-3 px-3.5">Negative Days</th>
                <th className="py-3 px-3.5">Days &lt; 5k</th>
                <th className="py-3 px-3.5">EMI Burden</th>
                <th className="py-3 px-3.5">Bounces</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.map((m) => (
                <tr
                  key={m.month}
                  onClick={() => setSelectedMonth(m)}
                  className="hover:bg-slate-50 cursor-pointer transition-colors"
                >
                  <td className="py-3 px-3.5 font-bold text-slate-800 whitespace-nowrap">{m.month}</td>
                  <td className="py-3 px-3.5 font-semibold text-blue-700">{formatCurrency(m.business_turnover)}</td>
                  <td className="py-3 px-3.5 text-slate-600">{formatCurrency(m.gross_credit)}</td>
                  <td className="py-3 px-3.5 text-slate-600">{formatCurrency(m.total_debit)}</td>
                  <td className={`py-3 px-3.5 font-medium ${m.net_flow >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                    {formatCurrency(m.net_flow)}
                  </td>
                  <td className="py-3 px-3.5 font-bold text-slate-900 bg-slate-50/50">{formatCurrency(m.abb)}</td>
                  <td className={`py-3 px-3.5 font-medium ${m.min_balance < 0 ? 'text-rose-600' : 'text-slate-700'}`}>
                    {formatCurrency(m.min_balance)}
                  </td>
                  <td className="py-3 px-3.5 text-slate-500 whitespace-nowrap">{formatDate(m.min_balance_date)}</td>
                  <td className="py-3 px-3.5 font-medium text-slate-700">{formatCurrency(m.month_end_balance)}</td>
                  <td className="py-3 px-3.5 text-center">
                    <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                      m.negative_days > 0 ? 'bg-rose-100 text-rose-800 font-bold' : 'text-slate-500'
                    }`}>
                      {m.negative_days}
                    </span>
                  </td>
                  <td className="py-3 px-3.5 text-center text-slate-600">{m.days_below_5000}</td>
                  <td className="py-3 px-3.5 font-semibold text-slate-800">{formatCurrency(m.emi_burden)}</td>
                  <td className="py-3 px-3.5 text-center">
                    {m.emi_bounce_count > 0 ? (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200">
                        {m.emi_bounce_count}
                      </span>
                    ) : (
                      <span className="text-slate-400">0</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Monthly Detail Modal */}
      {selectedMonth && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 border border-slate-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <h3 className="text-sm font-bold text-slate-800">Month Verification — {selectedMonth.month}</h3>
              <button onClick={() => setSelectedMonth(null)} className="p-1 hover:bg-slate-100 rounded text-slate-400">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Business Turnover</span>
                <span className="font-bold text-slate-800">{formatCurrency(selectedMonth.business_turnover)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Non-Business Credits Excluded</span>
                <span className="font-semibold text-slate-700">{formatCurrency(selectedMonth.non_business_credit)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Internal Transfers Excluded</span>
                <span className="font-semibold text-amber-700">{formatCurrency(selectedMonth.internal_transfer_credit_excluded)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Monthly ABB</span>
                <span className="font-bold text-blue-700">{formatCurrency(selectedMonth.abb)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">EMI-to-Turnover Ratio</span>
                <span className="font-bold text-slate-800">{formatPercentage(selectedMonth.emi_to_turnover_ratio)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Lowest Balance Date</span>
                <span className="text-slate-800 font-medium">{formatDate(selectedMonth.min_balance_date)} ({formatCurrency(selectedMonth.min_balance)})</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Negative Closing Days</span>
                <span className="font-bold text-rose-600">{selectedMonth.negative_days} days</span>
              </div>
            </div>
            <div className="mt-5 flex justify-end">
              <button onClick={() => setSelectedMonth(null)} className="px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-lg text-xs font-medium">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

