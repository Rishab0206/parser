import { apiFetch } from './client';

export interface AccountCard {
  account_id?: string;
  bank_name: string;
  account_no_masked: string;
  account_type: string;
  period_from?: string;
  period_to?: string;
  abb: number;
  turnover: number;
  emi_count: number;
  status: string;
  is_consolidated: boolean;
}

export function getAccounts(applicationId: string): Promise<AccountCard[]> {
  return apiFetch<AccountCard[]>(`/api/applications/${applicationId}/accounts`);
}

