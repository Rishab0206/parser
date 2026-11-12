import { apiFetch } from './client';

export interface ReturnRecord {
  id: string;
  original_emi_date?: string;
  lender_name: string;
  emi_amount: number;
  return_date: string;
  return_amount: number;
  return_charge_amount: number;
  charge_txn_id?: string;
  reason: string;
  recovery_status: string;
  recovery_txn_id?: string;
  source_page_no: number;
  original_txn_narration?: string;
  return_txn_narration?: string;
  ref_no?: string;
}

export function getReturns(applicationId: string): Promise<ReturnRecord[]> {
  return apiFetch<ReturnRecord[]>(`/api/applications/${applicationId}/returns`);
}

