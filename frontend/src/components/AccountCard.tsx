import React from 'react';
import { Building2, Layers, CheckCircle2, Clock } from 'lucide-react';
import { AccountCard as AccountCardType } from '../api/accounts';
import { formatCurrency, formatDate } from '../utils/format';

interface AccountCardProps {
  account: AccountCardType;
  isSelected: boolean;
  onSelect: () => void;
}

export const AccountCard: React.FC<AccountCardProps> = ({ account, isSelected, onSelect }) => {
  return (
    <div
      onClick={onSelect}
      className={`cursor-pointer rounded-xl p-4 transition-all border ${
        isSelected
          ? 'bg-blue-50/70 border-blue-500 shadow-sm ring-1 ring-blue-500'
          : 'bg-white border-slate-200 hover:border-slate-300 shadow-sm'
      }`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <div className={`p-2 rounded-lg ${isSelected ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600'}`}>
            {account.is_consolidated ? <Layers className="w-4 h-4" /> : <Building2 className="w-4 h-4" />}
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-800 line-clamp-1">{account.bank_name}</h4>
            <div className="flex items-center gap-2 text-xs text-slate-500 font-mono">
              <span>{account.account_no_masked}</span>
              <span className="text-slate-300">•</span>
              <span className="font-sans px-1.5 py-0.5 rounded text-[10px] bg-slate-100 text-slate-600 font-semibold uppercase">
                {account.account_type}
              </span>
            </div>
          </div>
        </div>
        <span className={`inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full font-medium ${
          account.status === 'PARSED'
            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
            : account.status === 'PARSING_FAILED' || account.status === 'INVALID_FILE' || account.status === 'FAILED'
            ? 'bg-rose-50 text-rose-700 border border-rose-200'
            : 'bg-amber-50 text-amber-700 border border-amber-200'
        }`}>
          {account.status === 'PARSED' ? <CheckCircle2 className="w-3 h-3" /> : <Clock className="w-3 h-3" />}
          {account.status}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-slate-100 mt-2">
        <div>
          <span className="text-slate-400 block text-[11px]">Turnover</span>
          <span className="font-semibold text-slate-700">
            {account.turnover !== null && account.turnover !== undefined ? formatCurrency(account.turnover) : 'Unavailable'}
          </span>
        </div>
        <div>
          <span className="text-slate-400 block text-[11px]">Monthly ABB</span>
          <span className="font-semibold text-slate-700">
            {account.abb !== null && account.abb !== undefined ? formatCurrency(account.abb) : 'Unavailable'}
          </span>
        </div>
      </div>

      <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-50 text-[11px] text-slate-400">
        <span>Period: {formatDate(account.period_from)} – {formatDate(account.period_to)}</span>
        <span>{account.emi_count} EMIs</span>
      </div>
    </div>
  );
};

