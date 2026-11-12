import React, { useState, useMemo } from 'react';
import { CustomerHistoryItem } from '../api/statements';
import { Search, Eye, Download, Building, Calendar, AlertTriangle, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { formatCurrency } from '../utils/format';

interface CustomerHistoryTableProps {
  history: CustomerHistoryItem[];
  onSelectCustomer: (applicationId: string) => void;
  onExportCustomer?: (applicationId: string) => void;
}

export const CustomerHistoryTable: React.FC<CustomerHistoryTableProps> = ({
  history,
  onSelectCustomer,
  onExportCustomer
}) => {
  const [search, setSearch] = useState('');
  const [bankFilter, setBankFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Distinct banks for filter
  const distinctBanks = useMemo(() => {
    const banks = new Set<string>();
    history.forEach((h) => {
      if (h.bank_name && h.bank_name !== '—') {
        h.bank_name.split(',').forEach((b) => banks.add(b.trim()));
      }
    });
    return Array.from(banks);
  }, [history]);

  // Filtered rows
  const filtered = useMemo(() => {
    return history.filter((h) => {
      const matchSearch =
        search === '' ||
        h.customer_name.toLowerCase().includes(search.toLowerCase()) ||
        h.bank_name.toLowerCase().includes(search.toLowerCase()) ||
        h.account_no_masked.toLowerCase().includes(search.toLowerCase());

      const matchBank =
        bankFilter === 'ALL' ||
        h.bank_name.toLowerCase().includes(bankFilter.toLowerCase());

      const matchStatus =
        statusFilter === 'ALL' ||
        h.status.toUpperCase() === statusFilter.toUpperCase();

      return matchSearch && matchBank && matchStatus;
    });
  }, [history, search, bankFilter, statusFilter]);

  return (
    <div className="space-y-4">
      {/* Search and Filters Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search Customer Name, Bank, Account No..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div className="flex items-center gap-2.5 w-full sm:w-auto">
          {/* Bank Filter */}
          <select
            value={bankFilter}
            onChange={(e) => setBankFilter(e.target.value)}
            className="py-2 px-3 bg-slate-50 border border-slate-300 rounded-lg text-slate-700 font-medium"
          >
            <option value="ALL">All Banks</option>
            {distinctBanks.map((b) => (
              <option key={b} value={b}>{b}</option>
            ))}
          </select>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="py-2 px-3 bg-slate-50 border border-slate-300 rounded-lg text-slate-700 font-medium"
          >
            <option value="ALL">All Status</option>
            <option value="PARSED">Parsed</option>
            <option value="NEEDS_REVIEW">Needs Review</option>
            <option value="ACTIVE">Active</option>
          </select>

          <span className="text-slate-500 font-semibold pl-2">
            Total: {filtered.length} Customer{filtered.length !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {/* History Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[11px]">
              <tr>
                <th className="py-3.5 px-4">Customer Name</th>
                <th className="py-3.5 px-3">Bank(s)</th>
                <th className="py-3.5 px-3">Account No.</th>
                <th className="py-3.5 px-3">Period</th>
                <th className="py-3.5 px-3 text-right">Turnover</th>
                <th className="py-3.5 px-3 text-right">Avg ABB</th>
                <th className="py-3.5 px-3 text-right">EMI / Month</th>
                <th className="py-3.5 px-3 text-center">EMI Bounce</th>
                <th className="py-3.5 px-3 text-center">ACH / ECS Return</th>
                <th className="py-3.5 px-3">Status</th>
                <th className="py-3.5 px-3">Date</th>
                <th className="py-3.5 px-4 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={12} className="py-8 text-center text-slate-400">
                    No customer history records found.
                  </td>
                </tr>
              ) : (
                filtered.map((item) => (
                  <tr
                    key={item.application_id}
                    onClick={() => onSelectCustomer(item.application_id)}
                    className="hover:bg-blue-50/60 transition-colors cursor-pointer group"
                  >
                    {/* Customer Name */}
                    <td className="py-3.5 px-4 font-bold text-slate-900 group-hover:text-blue-600">
                      <div className="flex items-center gap-1.5">
                        <span>{item.customer_name}</span>
                      </div>
                    </td>

                    {/* Bank */}
                    <td className="py-3.5 px-3 text-slate-700 font-medium">
                      <div className="flex items-center gap-1.5">
                        <Building className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        <span>{item.bank_name}</span>
                      </div>
                    </td>

                    {/* Masked Account No */}
                    <td className="py-3.5 px-3 font-mono font-semibold text-slate-800">
                      {item.account_no_masked}
                    </td>

                    {/* Period */}
                    <td className="py-3.5 px-3 text-slate-500 whitespace-nowrap">
                      {item.period}
                    </td>

                    {/* Turnover */}
                    <td className="py-3.5 px-3 text-right font-semibold text-slate-900 whitespace-nowrap">
                      ₹{item.turnover.toLocaleString('en-IN')}
                    </td>

                    {/* Avg ABB */}
                    <td className="py-3.5 px-3 text-right font-semibold text-slate-800 whitespace-nowrap">
                      ₹{item.avg_abb.toLocaleString('en-IN')}
                    </td>

                    {/* EMI / Month */}
                    <td className="py-3.5 px-3 text-right font-medium text-slate-700 whitespace-nowrap">
                      {item.emi_monthly > 0 ? `₹${item.emi_monthly.toLocaleString('en-IN')}` : '₹0'}
                    </td>

                    {/* EMI Bounce */}
                    <td className="py-3.5 px-3 text-center">
                      {item.emi_bounce > 0 ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800">
                          {item.emi_bounce}
                        </span>
                      ) : (
                        <span className="text-slate-400 font-medium">0</span>
                      )}
                    </td>

                    {/* ACH / ECS Return */}
                    <td className="py-3.5 px-3 text-center">
                      {item.ach_ecs_return > 0 ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800">
                          {item.ach_ecs_return}
                        </span>
                      ) : (
                        <span className="text-slate-400 font-medium">0</span>
                      )}
                    </td>

                    {/* Status */}
                    <td className="py-3.5 px-3 whitespace-nowrap">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold ${
                        item.status === 'PARSED'
                          ? 'bg-emerald-100 text-emerald-800'
                          : item.status === 'NEEDS_REVIEW'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-slate-100 text-slate-700'
                      }`}>
                        {item.status === 'PARSED' ? (
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                        ) : (
                          <AlertTriangle className="w-3 h-3 text-amber-600" />
                        )}
                        {item.status}
                      </span>
                    </td>

                    {/* Date */}
                    <td className="py-3.5 px-3 text-slate-500 whitespace-nowrap text-[11px]">
                      {item.created_at}
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-4 text-center whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-center gap-1.5">
                        <button
                          onClick={() => onSelectCustomer(item.application_id)}
                          className="px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded font-semibold text-[11px] inline-flex items-center gap-1 shadow-xs transition-colors"
                          title="View complete customer analysis"
                        >
                          <Eye className="w-3 h-3" />
                          View
                        </button>
                        {onExportCustomer && (
                          <button
                            onClick={() => onExportCustomer(item.application_id)}
                            className="px-2 py-1 border border-slate-300 hover:bg-slate-100 text-slate-700 rounded font-semibold text-[11px] inline-flex items-center gap-1 transition-colors"
                            title="Export verified data"
                          >
                            <Download className="w-3 h-3" />
                            Export
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

