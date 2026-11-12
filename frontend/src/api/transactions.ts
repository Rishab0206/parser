import { apiFetch } from './client';

export interface TransactionItem {
  id: string;
  statement_id: string;
  txn_date: string;
  value_date?: string;
  narration_raw: string;
  narration_clean?: string;
  ref_no?: string;
  utr?: string;
  debit: number;
  credit: number;
  balance: number;
  channel: string;
  counterparty?: string;
  category: string;
  confidence: number;
  source_page_no: number;
  is_duplicate: boolean;
  is_internal_transfer: boolean;
  internal_match_id?: string;
  statement_bank?: string;
  statement_account_masked?: string;
}

export interface TransactionListResponse {
  items: TransactionItem[];
  total: number;
  page: number;
  page_size: number;
}

export function getTransactions(
  applicationId: string,
  params: {
    search?: string;
    bank?: string;
    month?: string;
    channel?: string;
    category?: string;
    account_id?: string;
    page?: number;
    page_size?: number;
  }
): Promise<TransactionListResponse> {
  const query = new URLSearchParams();
  if (params.search) query.append('search', params.search);
  if (params.bank) query.append('bank', params.bank);
  if (params.month) query.append('month', params.month);
  if (params.channel) query.append('channel', params.channel);
  if (params.category) query.append('category', params.category);
  if (params.account_id) query.append('account_id', params.account_id);
  query.append('page', String(params.page || 1));
  query.append('page_size', String(params.page_size || 25));

  return apiFetch<TransactionListResponse>(`/api/applications/${applicationId}/transactions?${query.toString()}`);
}

