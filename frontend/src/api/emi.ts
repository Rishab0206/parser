import { apiFetch } from './client';

export interface EmiRecord {
  id: string;
  lender_name: string;
  lender_confidence: string; // CONFIRMED, PROBABLE, POSSIBLE
  mandate_ref?: string;
  amount: number;
  frequency: string;
  first_date?: string;
  last_date?: string;
  total_attempts: number;
  total_success: number;
  total_returns: number;
  status: string;
  latest_mode: string;
  latest_date?: string;
  masked_account?: string;
  bank_name?: string;
}

export interface EmiAttempt {
  id: string;
  attempt_date: string;
  amount: number;
  status: string;
  return_id?: string;
  transaction_id: string;
  narration_raw?: string;
  source_page_no?: number;
  ref_no?: string;
}

export interface EmiDetail {
  emi_record: EmiRecord;
  attempts: EmiAttempt[];
  bounce_rate: number;
  last_3_attempts: EmiAttempt[];
  recovery_info?: {
    total_returns: number;
    recovered_count: number;
    recovery_rate_pct: number;
  };
}

export function getEmis(applicationId: string): Promise<EmiRecord[]> {
  return apiFetch<EmiRecord[]>(`/api/applications/${applicationId}/emi`);
}

export function getEmiDetail(applicationId: string, emiId: string): Promise<EmiDetail> {
  return apiFetch<EmiDetail>(`/api/applications/${applicationId}/emi/${emiId}`);
}

