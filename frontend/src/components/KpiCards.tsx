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

  const cards = [
    {
      title: "Total Business Turnover",
      value: hasData ? formatCurrency(summary.total_business_turnover) : "—",
      subtext: hasData ? `Excl. internal trf: ${formatCurrency(summary.internal_transfers_excluded)}` : "Upload statement",
      icon: TrendingUp,
      color: "text-blue-600 bg-blue-50 border-blue-100",
    },
    {
      title: "Avg Monthly Turnover",
      value: hasData ? formatCurrency(summary.avg_monthly_turnover) : "—",
      subtext: hasData ? "Verified business sales" : "Upload statement",
      icon: DollarSign,
      color: "text-indigo-600 bg-indigo-50 border-indigo-100",
    },
    {
      title: "Total Debit",
      value: hasData ? formatCurrency(summary.total_debit) : "—",
      subtext: hasData ? "Expenses & payouts" : "Upload statement",
      icon: TrendingDown,
      color: "text-slate-600 bg-slate-50 border-slate-100",
    },
    {
      title: "Net Cash Flow",
      value: hasData ? formatCurrency(summary.net_cash_flow) : "—",
      subtext: hasData ? (summary.net_cash_flow >= 0 ? "Positive operating flow" : "Negative net flow") : "Upload statement",
      icon: summary.net_cash_flow >= 0 ? ArrowUpRight : ArrowDownRight,
      color: summary.net_cash_flow >= 0 ? "text-emerald-600 bg-emerald-50 border-emerald-100" : "text-rose-600 bg-rose-50 border-rose-100",
    },
    {
      title: "Avg Monthly ABB",
      value: hasData ? formatCurrency(summary.avg_monthly_abb) : "—",
      subtext: hasData ? "Daily EOD carry-forward" : "Upload statement",
      icon: Wallet,
      color: "text-cyan-600 bg-cyan-50 border-cyan-100",
    },
    {
      title: "EMI Bounce / ECS Returns",
      value: hasData ? String(summary.emi_bounce_count) : "—",
      subtext: hasData ? `${summary.total_ecs_returns} return records verified` : "Upload statement",
      icon: AlertOctagon,
      color: (hasData && summary.emi_bounce_count > 0) ? "text-rose-600 bg-rose-50 border-rose-200" : "text-slate-600 bg-slate-50 border-slate-100",
    },
    {
      title: "EMI-to-Turnover Ratio",
      value: hasData ? formatPercentage(summary.emi_to_turnover_ratio) : "—",
      subtext: hasData ? "Verified EMI burden vs turnover" : "Upload statement",
      icon: Percent,
      color: "text-violet-600 bg-violet-50 border-violet-100",
      badge: "Not FOIR"
    },
    {
      title: "Negative Days",
      value: hasData ? String(summary.total_negative_days) : "—",
      subtext: hasData ? "Days closing below ₹0" : "Upload statement",
      icon: CalendarX,
      color: (hasData && summary.total_negative_days > 0) ? "text-amber-600 bg-amber-50 border-amber-200" : "text-slate-600 bg-slate-50 border-slate-100",
    },
    {
      title: "Review Queue",
      value: hasData ? String(summary.review_queue_count) : "—",
      subtext: hasData ? (summary.review_queue_count > 0 ? "Requires underwriter action" : "All clean") : "Upload statement",
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
              className={`bg-white rounded-xl p-4 border border-slate-200 shadow-sm relative transition-all ${
                c.isAction ? 'cursor-pointer hover:border-amber-400 hover:shadow-md' : ''
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

      {hasData && summary.internal_transfers_excluded > 0 && (
        <div className="flex items-center gap-2 p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-xs mb-4">
          <Info className="w-4 h-4 text-amber-600 flex-shrink-0" />
          <span>
            <strong>Internal Transfers Excluded:</strong> {formatCurrency(summary.internal_transfers_excluded)} reconciled across applicant accounts and excluded from Consolidated Business Turnover.
          </span>
        </div>
      )}
    </div>
  );
};

