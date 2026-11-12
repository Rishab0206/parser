import React, { useState } from 'react';
import { ReviewQueueItem, resolveReviewItem } from '../api/review';
import { formatCurrency, formatDate } from '../utils/format';
import { CheckCircle2, XCircle, Edit3, AlertTriangle, ShieldAlert } from 'lucide-react';

interface ReviewQueueTableProps {
  items: ReviewQueueItem[];
  onResolved: () => void;
}

export const ReviewQueueTable: React.FC<ReviewQueueTableProps> = ({ items, onResolved }) => {
  const [selectedItem, setSelectedItem] = useState<ReviewQueueItem | null>(null);
  const [actionType, setActionType] = useState<'APPROVED' | 'REJECTED' | 'CORRECTED'>('APPROVED');
  const [reason, setReason] = useState<string>('');
  const [correctedAmount, setCorrectedAmount] = useState<string>('');
  const [correctedCategory, setCorrectedCategory] = useState<string>('BUSINESS_RECEIPT');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const handleOpenResolve = (item: ReviewQueueItem, action: 'APPROVED' | 'REJECTED' | 'CORRECTED') => {
    setSelectedItem(item);
    setActionType(action);
    setReason('');
    setCorrectedAmount(item.amount ? String(item.amount) : '');
  };

  const handleSubmitResolve = async () => {
    if (!selectedItem) return;
    if (!reason) {
      alert("Please provide an underwriter reason for this resolution (mandatory for audit).");
      return;
    }

    setIsSubmitting(true);
    try {
      const correctedObj = actionType === 'CORRECTED' ? {
        debit: parseFloat(correctedAmount) || 0.0,
        credit: 0.0,
        category: correctedCategory
      } : undefined;

      await resolveReviewItem(selectedItem.id, actionType, reason, correctedObj);
      setSelectedItem(null);
      onResolved();
    } catch (e: any) {
      alert("Resolution error: " + (e.message || "Failed"));
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!items || items.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-500 text-sm">
        Review Queue is clear. All transactions passed automated confidence checks.
      </div>
    );
  }

  return (
    <>
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="p-3.5 bg-amber-50 border-b border-amber-200 flex items-center gap-2 text-xs text-amber-900">
          <ShieldAlert className="w-4 h-4 text-amber-600 flex-shrink-0" />
          <span>
            <strong>Review Queue:</strong> Transactions with confidence &lt;70%, balance discrepancies, or cross-account ambiguities are routed here. Every approved change is versioned and logged.
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-medium">
              <tr>
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4">Issue Type</th>
                <th className="py-3 px-4">Confidence</th>
                <th className="py-3 px-4">Raw Narration / Details</th>
                <th className="py-3 px-4">Amount</th>
                <th className="py-3 px-4">Source</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((it) => (
                <tr key={it.id} className="hover:bg-slate-50">
                  <td className="py-3 px-4 whitespace-nowrap text-slate-700">{formatDate(it.date)}</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-100 text-amber-900 border border-amber-200 uppercase">
                      {it.issue_type}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="font-semibold text-rose-600">{it.confidence}%</span>
                  </td>
                  <td className="py-3 px-4 max-w-xs truncate font-mono text-[11px] text-slate-800" title={it.narration_raw}>
                    {it.narration_raw || JSON.stringify(it.suggested_value)}
                  </td>
                  <td className="py-3 px-4 font-bold text-slate-900">{formatCurrency(it.amount)}</td>
                  <td className="py-3 px-4 text-slate-400 whitespace-nowrap">p.{it.source_page_no || 1}</td>
                  <td className="py-3 px-4 text-right space-x-1.5 whitespace-nowrap">
                    <button
                      onClick={() => handleOpenResolve(it, 'APPROVED')}
                      className="px-2.5 py-1 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 rounded font-semibold text-[11px]"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => handleOpenResolve(it, 'CORRECTED')}
                      className="px-2.5 py-1 bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 rounded font-semibold text-[11px]"
                    >
                      Correct
                    </button>
                    <button
                      onClick={() => handleOpenResolve(it, 'REJECTED')}
                      className="px-2.5 py-1 bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200 rounded font-semibold text-[11px]"
                    >
                      Reject
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Resolution Dialog */}
      {selectedItem && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 border border-slate-200 animate-in zoom-in-95 duration-150 text-xs">
            <h3 className="text-sm font-bold text-slate-800 mb-1">
              Underwriter Action: {actionType}
            </h3>
            <p className="text-slate-500 mb-4 text-[11px]">
              Item: {selectedItem.issue_type} (Confidence {selectedItem.confidence}%)
            </p>

            <div className="space-y-3">
              {actionType === 'CORRECTED' && (
                <>
                  <div>
                    <label className="block text-slate-600 font-medium mb-1">Corrected Amount (₹)</label>
                    <input
                      type="number"
                      value={correctedAmount}
                      onChange={(e) => setCorrectedAmount(e.target.value)}
                      className="w-full p-2 border border-slate-300 rounded-lg text-slate-900 font-semibold"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-600 font-medium mb-1">Corrected Category</label>
                    <select
                      value={correctedCategory}
                      onChange={(e) => setCorrectedCategory(e.target.value)}
                      className="w-full p-2 border border-slate-300 rounded-lg text-slate-900"
                    >
                      <option value="BUSINESS_RECEIPT">Business Receipt</option>
                      <option value="GENERAL_EXPENSE">General Expense</option>
                      <option value="INTERNAL_TRANSFER">Internal Transfer</option>
                      <option value="LOAN_DISBURSAL">Loan Disbursal</option>
                      <option value="BANK_CHARGES">Bank Charges</option>
                    </select>
                  </div>
                </>
              )}

              <div>
                <label className="block text-slate-600 font-medium mb-1">
                  Reason for Resolution <span className="text-rose-500">*</span>
                </label>
                <textarea
                  rows={3}
                  placeholder="Document source page confirmation, verified by underwriter..."
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded-lg text-slate-900"
                />
              </div>
            </div>

            <div className="mt-5 flex justify-end gap-2 border-t border-slate-100 pt-3">
              <button
                disabled={isSubmitting}
                onClick={() => setSelectedItem(null)}
                className="px-3 py-1.5 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg font-medium"
              >
                Cancel
              </button>
              <button
                disabled={isSubmitting}
                onClick={handleSubmitResolve}
                className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold"
              >
                {isSubmitting ? 'Saving...' : 'Confirm Resolution'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

