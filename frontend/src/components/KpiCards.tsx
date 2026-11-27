import React from 'react';
import { 
  TrendingUp, TrendingDown, DollarSign, Wallet, AlertOctagon, 
  AlertTriangle, Percent, CalendarX, ArrowUpRight, ArrowDownRight, Info
} from 'lucide-react';
import { SummaryKpis } from '../api/abb';
import { formatCurrency, formatPercentage } from '../utils/format';

interface KpiCardsProps {
  summary: SummaryKpis;
  onReviewClick?: () => void;
}

export const KpiCards: React.FC<KpiCardsProps> = ({ summary, onReviewClick }) => {
  const hasData = summary.has_data;
  const fmtOrNa = (val: number | null | undefined) =>
    hasData && val !== null && val !== undefined ? formatCurrency(val) : 'Not Available';
  const numOrNa = (val: number | null | undefined) =>
    hasData && val !== null && val !== undefined ? String(val) : 'Not Available';

  const netCashFlow = summary.net_cash_flow ?? 0;
  const emiBounces = summary.emi_bounce_count ?? 0;
  const negDays = summary.total_negative_days ?? 0;
  const internalExcluded = summary.internal_transfers_excluded ?? 0;

  const cards = [
    {
      title: "Total Credits",
      value: fmtOrNa(summary.total_credits),
      subtext: hasData ? "Verified gross inflows" : "Not Available",
      icon: ArrowUpRight,
      color: "text-emerald-600 bg-emerald-50 border-emerald-100",
    },
    {
      title: "Total Debits",
      value: fmtOrNa(summary.total_debit),
      subtext: hasData ? "Expenses & payouts" : "Not Available",
      icon: TrendingDown,
      color: "text-slate-600 bg-slate-50 border-slate-100",
    },
    {
      title: "Closing Balance",
      value: fmtOrNa(summary.closing_balance),
      subtext: hasData && summary.opening_balance !== null && summary.opening_balance !== undefined
        ? `Opening: ${formatCurrency(summary.opening_balance)}`
        : "Not Available",
      icon: Wallet,
      color: "text-violet-600 bg-violet-50 border-violet-100",
    },
    {
      title: "Total Transactions",
      value: numOrNa(summary.total_transactions),
      subtext: hasData ? "Extracted & verified rows" : "Not Available",
      icon: DollarSign,
      color: "text-blue-600 bg-blue-50 border-blue-100",
    },
    {
      title: "Monthly Average Balance",
      value: fmtOrNa(summary.avg_monthly_abb),
      subtext: hasData ? "Daily EOD carry-forward" : "Not Available",
      icon: Wallet,
      color: "text-cyan-600 bg-cyan-50 border-cyan-100",
    },
    {
      title: "Monthly Turnover",
      value: fmtOrNa(summary.avg_monthly_turnover),
      subtext: hasData ? `Total: ${fmtOrNa(summary.total_business_turnover)}` : "Not Available",
      icon: TrendingUp,
      color: "text-indigo-600 bg-indigo-50 border-indigo-100",
    },
    {
      title: "Net Cash Flow",
      value: fmtOrNa(summary.net_cash_flow),
      subtext: hasData ? (netCashFlow >= 0 ? "Positive operating flow" : "Negative net flow") : "Not Available",
      icon: netCashFlow >= 0 ? ArrowUpRight : ArrowDownRight,
      color: netCashFlow >= 0 ? "text-emerald-600 bg-emerald-50 border-emerald-100" : "text-rose-600 bg-rose-50 border-rose-100",
    },
    {
      title: "EMI Bounce / ECS Returns",
      value: numOrNa(summary.emi_bounce_count),
      subtext: hasData ? `${summary.total_ecs_returns ?? 0} return records verified` : "Not Available",
      icon: AlertOctagon,
      color: (hasData && emiBounces > 0) ? "text-rose-600 bg-rose-50 border-rose-200" : "text-slate-600 bg-slate-50 border-slate-100",
    },
    {
      title: "EMI-to-Turnover Ratio",
      value: hasData && summary.emi_to_turnover_ratio !== null && summary.emi_to_turnover_ratio !== undefined
        ? formatPercentage(summary.emi_to_turnover_ratio)
        : "Not Available",
      subtext: hasData ? "Verified EMI burden vs turnover" : "Not Available",
      icon: Percent,
      color: "text-violet-600 bg-violet-50 border-violet-100",
      badge: "Not FOIR"
    },
    {
      title: "Review Queue",
      value: String(summary.review_queue_count ?? 0),
      subtext: hasData ? (summary.review_queue_count > 0 ? "Requires underwriter action" : "All clean") : "Not Available",
      icon: AlertTriangle,
      color: (hasData && summary.review_queue_count > 0) ? "text-amber-700 bg-amber-100 border-amber-300 ring-1 ring-amber-400" : "text-slate-600 bg-slate-50 border-slate-100",
      onClick: onReviewClick,
      isAction: hasData && summary.review_queue_count > 0
    }
  ];

  return (
    <div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3.5 mb-4">
        {cards.map((c, i) => {
          const Icon = c.icon;
          return (
            <div
              key={i}
              onClick={c.onClick}
              className={`bg-white/90 backdrop-blur-xs rounded-xl p-4 border border-slate-200 shadow-sm relative transition-all ${
                c.isAction ? 'cursor-pointer hover:border-amber-400 hover:shadow-md' : 'hover:border-blue-200'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-slate-500 line-clamp-1">{c.title}</span>
                <div className={`p-1.5 rounded-lg border ${c.color}`}>
                  <Icon className="w-3.5 h-3.5" />
                </div>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-xl font-bold text-slate-900 tracking-tight">{c.value}</span>
                {c.badge && (
                  <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-slate-100 text-slate-500">
                    {c.badge}
                  </span>
                )}
              </div>
              <p className="text-[11px] text-slate-400 mt-1 line-clamp-1 flex items-center gap-1">
                {c.subtext}
              </p>
            </div>
          );
        })}
      </div>

      {hasData && internalExcluded > 0 && (
        <div className="flex items-center gap-2 p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-xs mb-4">
          <Info className="w-4 h-4 text-amber-600 flex-shrink-0" />
          <span>
            <strong>Internal Transfers Excluded:</strong> {formatCurrency(internalExcluded)} reconciled across applicant accounts and excluded from Consolidated Business Turnover.
          </span>
        </div>
      )}

      {hasData && negDays > 0 && (
        <div className="flex items-center gap-2 p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-900 text-xs mb-4">
          <CalendarX className="w-4 h-4 text-rose-600 flex-shrink-0" />
          <span>
            <strong>Overdraft / Negative Balance Alert:</strong> {negDays} day(s) closed below ₹0 during the statement period.
          </span>
        </div>
      )}
    </div>
  );
};

