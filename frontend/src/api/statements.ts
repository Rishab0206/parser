import { apiFetch } from './client';

export interface StatementUploadResponse {
  statement_id: string;
  application_id?: string;
  customer_name?: string;
  status: string;
  file_name?: string;
  message?: string;
  is_duplicate?: boolean;
}

export interface StatementStatus {
  statement_id: string;
  status: string;
  bank_name?: string;
  bank_detect_confidence: number;
  account_no_masked?: string;
  account_type: string;
  page_count: number;
  rows_parsed: number;
  failed_rows_count?: number;
  confidence: number;
  review_queue_count: number;
  error_message?: string;
  error_report?: any;
}

export interface CustomerHistoryItem {
  application_id: string;
  customer_id: string;
  customer_name: string;
  bank_name: string;
  account_no_masked: string;
  period: string;
  turnover: number;
  avg_abb: number;
  emi_monthly: number;
  active_emi_count: number;
  emi_bounce: number;
  ach_ecs_return: number;
  statement_count: number;
  status: string;
  created_at: string;
}

export function uploadStatement(
  file: File,
  applicationId?: string,
  pdfPassword?: string,
  accountType?: string,
  customerName?: string
): Promise<StatementUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (applicationId) {
    formData.append('application_id', applicationId);
  }
  if (customerName) {
    formData.append('customer_name', customerName);
  }
  if (pdfPassword) {
    formData.append('pdf_password', pdfPassword);
  }
  if (accountType) {
    formData.append('account_type', accountType);
  }
  return apiFetch<StatementUploadResponse>('/api/statements/upload', {
    method: 'POST',
    body: formData,
  });
}

export function getCustomerHistory(): Promise<CustomerHistoryItem[]> {
  return apiFetch<CustomerHistoryItem[]>('/api/customer-history');
}

export function resetNewApplication(): Promise<{ id: string; customer_id: string; customer_name: string }> {
  return apiFetch<{ id: string; customer_id: string; customer_name: string }>('/api/applications/reset', {
    method: 'POST'
  });
}

export function getStatementStatus(statementId: string): Promise<StatementStatus> {
  return apiFetch<StatementStatus>(`/api/statements/${statementId}/status`);
}

export function getSupportedBanks(): Promise<any[]> {
  return apiFetch<any[]>('/api/banks/supported');
}

export function getApplications(): Promise<any[]> {
  return apiFetch<any[]>('/api/applications');
}

export function createApplication(name: string, phone: string): Promise<any> {
  return apiFetch<any>(`/api/applications?name=${encodeURIComponent(name)}&phone=${encodeURIComponent(phone)}`, {
    method: 'POST'
  });
}

