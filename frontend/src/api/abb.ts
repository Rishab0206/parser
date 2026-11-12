import { apiFetch } from './client';

export interface MonthlySummary {
  month: string;
  gross_credit: number;
  business_turnover: number;
  non_business_credit: number;
  internal_transfer_credit_excluded: number;
  total_debit: number;
  net_flow: number;
  abb: number;
  min_balance: number;
  max_balance: number;
  min_balance_date?: string;
  month_end_balance: number;
  negative_days: number;
  days_below_5000: number;
  days_below_10000: number;
  emi_burden: number;
  emi_bounce_count: number;
  emi_to_turnover_ratio: number;
}

export interface SummaryKpis {
  total_business_turnover: number;
  avg_monthly_turnover: number;
  total_debit: number;
  net_cash_flow: number;
  avg_monthly_abb: number;
  emi_bounce_count: number;
  total_ecs_returns: number;
  emi_to_turnover_ratio: number;
  total_negative_days: number;
  review_queue_count: number;
  internal_transfers_excluded: number;
  monthly_breakdown: MonthlySummary[];
  has_data: boolean;
}

export function getSummary(applicationId: string, accountId?: string): Promise<SummaryKpis> {
  const q = accountId ? `?account_id=${accountId}` : '';
  return apiFetch<SummaryKpis>(`/api/applications/${applicationId}/summary${q}`);
}

export function getAbbMonthly(applicationId: string, accountId?: string): Promise<MonthlySummary[]> {
  const q = accountId ? `?account_id=${accountId}` : '';
  return apiFetch<MonthlySummary[]>(`/api/applications/${applicationId}/abb${q}`);
}

