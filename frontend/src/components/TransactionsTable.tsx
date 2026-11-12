import React, { useState } from 'react';
import { TransactionItem } from '../api/transactions';
import { formatCurrency, formatDate } from '../utils/format';
import { Search, Filter, ShieldCheck, AlertCircle, X, ChevronLeft, ChevronRight } from 'lucide-react';

interface TransactionsTableProps {
  transactions: TransactionItem[];
  total: number;
  page: number;
  pageSize: number;
  search: string;
  channel: string;
  category: string;
  onSearchChange: (val: string) => void;
  onChannelChange: (val: string) => void;
  onCategoryChange: (val: string) => void;
  onPageChange: (newPage: number) => void;
}

export const TransactionsTable: React.FC<TransactionsTableProps> = ({
  transactions,
  total,
  page,
  pageSize,
  search,
  channel,
  category,
  onSearchChange,
  onChannelChange,
  onCategoryChange,
  onPageChange,
}) => {
  const [selectedTxn, setSelectedTxn] = useState<TransactionItem | null>(null);

  const totalPages = Math.ceil(total / pageSize);

  return (
    <>
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
        {/* Filters Bar */}
        <div className="p-3.5 border-b border-slate-200 bg-slate-50/70 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 flex-1 min-w-[220px] max-w-md">
            <div className="relative w-full">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search narration, ref, or payee..."
                value={search}
                onChange={(e) => onSearchChange(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={channel}
              onChange={(e) => onChannelChange(e.target.value)}
              className="py-1.5 px-2.5 text-xs bg-white border border-slate-300 rounded-lg text-slate-700"
            >
              <option value="ALL">All Channels</option>
              <option value="UPI">UPI</option>
              <option value="NEFT">NEFT</option>
              <option value="RTGS">RTGS</option>
              <option value="IMPS">IMPS</option>
              <option value="NACH">NACH</option>
              <option value="CHEQUE">Cheque</option>
              <option value="CASH">Cash</option>
            </select>

            <select
              value={category}
              onChange={(e) => onCategoryChange(e.target.value)}
              className="py-1.5 px-2.5 text-xs bg-white border border-slate-300 rounded-lg text-slate-700"
            >
              <option value="ALL">All Categories</option>
              <option value="BUSINESS_RECEIPT">Business Receipt</option>
              <option value="GENERAL_EXPENSE">General Expense</option>
              <option value="LOAN_DISBURSAL">Loan Disbursal</option>
              <option value="FD_MATURITY">FD Maturity</option>
              <option value="REVERSAL_REFUND">Reversal/Refund</option>
              <option value="INTERNAL_TRANSFER">Internal Transfer</option>
              <option value="BANK_CHARGES">Bank Charges</option>
            </select>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-medium">
              <tr>
                <th className="py-3 px-3.5">Date</th>
                <th className="py-3 px-3.5">Narration</th>
                <th className="py-3 px-3.5">Ref / UTR</th>
                <th className="py-3 px-3.5">Channel</th>
                <th className="py-3 px-3.5">Category</th>
                <th className="py-3 px-3.5 text-right">Debit (Dr)</th>
                <th className="py-3 px-3.5 text-right">Credit (Cr)</th>
                <th className="py-3 px-3.5 text-right font-bold text-slate-900">Balance</th>
                <th className="py-3 px-3.5">Source</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {transactions.map((t) => (
                <tr
                  key={t.id}
                  onClick={() => setSelectedTxn(t)}
                  className="hover:bg-slate-50 cursor-pointer transition-colors"
                >
                  <td className="py-2.5 px-3.5 whitespace-nowrap text-slate-700 font-medium">{formatDate(t.txn_date)}</td>
                  <td className="py-2.5 px-3.5 max-w-sm truncate text-slate-800 font-mono text-[11px]" title={t.narration_raw}>
                    {t.narration_raw}
                  </td>
                  <td className="py-2.5 px-3.5 text-slate-500 font-mono text-[11px] whitespace-nowrap">{t.ref_no || "—"}</td>
                  <td className="py-2.5 px-3.5 whitespace-nowrap">
                    <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-100 text-slate-700 font-medium font-mono">
                      {t.channel}
                    </span>
                  </td>
                  <td className="py-2.5 px-3.5 whitespace-nowrap">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                      t.category === 'BUSINESS_RECEIPT' ? 'bg-blue-50 text-blue-700 border border-blue-200' :
                      t.category === 'LOAN_DISBURSAL' ? 'bg-purple-50 text-purple-700' :
                      t.is_internal_transfer ? 'bg-amber-50 text-amber-800 border border-amber-200' : 'bg-slate-100 text-slate-600'
                    }`}>
                      {t.is_internal_transfer ? 'INTERNAL TRANSFER' : t.category}
                    </span>
                  </td>
                  <td className="py-2.5 px-3.5 text-right font-medium text-rose-700 whitespace-nowrap">
                    {t.debit > 0 ? formatCurrency(t.debit) : "—"}
                  </td>
                  <td className="py-2.5 px-3.5 text-right font-medium text-emerald-700 whitespace-nowrap">
                    {t.credit > 0 ? formatCurrency(t.credit) : "—"}
                  </td>
                  <td className="py-2.5 px-3.5 text-right font-bold text-slate-900 whitespace-nowrap">
                    {formatCurrency(t.balance)}
                  </td>
                  <td className="py-2.5 px-3.5 text-slate-400 whitespace-nowrap">p.{t.source_page_no}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-3 border-t border-slate-200 bg-slate-50/50 flex items-center justify-between text-xs text-slate-600">
          <span>
            Showing {transactions.length > 0 ? (page - 1) * pageSize + 1 : 0} to {Math.min(page * pageSize, total)} of {total} transactions
          </span>
          <div className="flex items-center gap-1.5">
            <button
              disabled={page <= 1}
              onClick={() => onPageChange(page - 1)}
              className="p-1 rounded border border-slate-300 disabled:opacity-40 hover:bg-slate-100"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-2 font-medium">Page {page} of {totalPages || 1}</span>
            <button
              disabled={page >= totalPages}
              onClick={() => onPageChange(page + 1)}
              className="p-1 rounded border border-slate-300 disabled:opacity-40 hover:bg-slate-100"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Transaction Detail Drawer */}
      {selectedTxn && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-lg bg-white h-full shadow-2xl flex flex-col p-6 animate-in slide-in-from-right duration-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <h3 className="text-base font-bold text-slate-800">Transaction Verification</h3>
              <button onClick={() => setSelectedTxn(null)} className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto py-4 space-y-4 text-xs">
              <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-1">
                <span className="text-[11px] text-slate-400 font-medium uppercase">Raw Narration from PDF</span>
                <p className="font-mono text-slate-800 text-xs break-all leading-relaxed bg-white p-2.5 rounded border border-slate-200">
                  {selectedTxn.narration_raw}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <span className="text-slate-400 block text-[11px]">Date</span>
                  <span className="font-semibold text-slate-800">{formatDate(selectedTxn.txn_date)}</span>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <span className="text-slate-400 block text-[11px]">Source Page</span>
                  <span className="font-semibold text-slate-800">Page {selectedTxn.source_page_no}</span>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <span className="text-slate-400 block text-[11px]">Debit (Dr)</span>
                  <span className="font-bold text-rose-700">{formatCurrency(selectedTxn.debit)}</span>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <span className="text-slate-400 block text-[11px]">Credit (Cr)</span>
                  <span className="font-bold text-emerald-700">{formatCurrency(selectedTxn.credit)}</span>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <span className="text-slate-400 block text-[11px]">Running Balance</span>
                  <span className="font-bold text-slate-900">{formatCurrency(selectedTxn.balance)}</span>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <span className="text-slate-400 block text-[11px]">Payment Channel</span>
                  <span className="font-mono font-medium text-slate-800">{selectedTxn.channel}</span>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 col-span-2">
                  <span className="text-slate-400 block text-[11px]">Counterparty / Payee</span>
                  <span className="font-semibold text-slate-800">{selectedTxn.counterparty || "—"}</span>
                </div>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
                <span className="text-slate-400 block text-[11px]">Category Classification</span>
                <span className="font-semibold text-slate-800">{selectedTxn.category}</span>
                {selectedTxn.is_internal_transfer && (
                  <p className="text-amber-700 text-[11px] mt-1">
                    Marked as Internal Own-Account Transfer (Internal Match ID: {selectedTxn.internal_match_id})
                  </p>
                )}
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 flex items-center justify-between">
                <span className="text-slate-500">Confidence Score:</span>
                <span className="font-bold text-slate-800">{selectedTxn.confidence}%</span>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-200 flex justify-end">
              <button
                onClick={() => setSelectedTxn(null)}
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

