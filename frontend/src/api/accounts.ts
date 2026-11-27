import { apiFetch } from './client';

export interface AccountCard {
  account_id?: string;
  bank_name: string;
  account_no_masked: string;
  account_type: string;
  ifsc?: string;
  period_from?: string;
  period_to?: string;
  abb: number | null;
  turnover: number | null;
  opening_balance?: number | null;
  closing_balance?: number | null;
  reconciliation_status?: string | null;
  reconciliation_diff?: number | null;
  emi_count: number;
  status: string;
  error_message?: string | null;
  is_consolidated: boolean;
}

export function getAccounts(applicationId: string): Promise<AccountCard[]> {
  return apiFetch<AccountCard[]>(`/api/applications/${applicationId}/accounts`);
}

