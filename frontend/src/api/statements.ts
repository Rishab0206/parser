import { apiFetch } from './client';

export interface PdfInspectionResult {
  is_valid: boolean;
  is_encrypted: boolean;
  is_scanned: boolean;
  has_extractable_text: boolean;
  page_count: number;
  file_status: 'FILE_UPLOADED' | 'PASSWORD_REQUIRED' | 'INVALID_FILE';
  classification: string;
  message: string;
}

export interface StatementUploadResponse {
  statement_id: string;
  application_id?: string;
  customer_name?: string;
  status: string;
  is_encrypted?: boolean;
  error_message?: string;
  file_name?: string;
  message?: string;
  is_duplicate?: boolean;
}

export interface StatementStatus {
  statement_id: string;
  status: string;
  processing_stage?: string;
  bank_name?: string;
  bank_detect_confidence: number;
  account_no_masked?: string;
  account_type: string;
  ifsc?: string;
  customer_name?: string;
  period_from?: string;
  period_to?: string;
  page_count: number;
  rows_parsed: number;
  failed_rows_count?: number;
  confidence: number;
  review_queue_count: number;
  opening_balance?: number | null;
  closing_balance?: number | null;
  expected_closing_balance?: number | null;
  reconciliation_diff?: number | null;
  reconciliation_status?: string | null;
  total_credits?: number | null;
  total_debits?: number | null;
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
  turnover: number | null;
  avg_abb: number | null;
  emi_monthly: number;
  active_emi_count: number;
  emi_bounce: number;
  ach_ecs_return: number;
  statement_count: number;
  status: string;
  created_at: string;
}

export function inspectStatementFile(file: File): Promise<PdfInspectionResult> {
  const formData = new FormData();
  formData.append('file', file);
  return apiFetch<PdfInspectionResult>('/api/statements/inspect', {
    method: 'POST',
    body: formData,
    timeoutMs: 60000,
  });
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
    timeoutMs: 90000,
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
  return apiFetch<StatementStatus>(`/api/statements/${statementId}/status`, {
    timeoutMs: 15000,
  });
}

export function unlockStatement(
  statementId: string,
  password: string
): Promise<any> {
  return apiFetch<any>(`/api/statements/${statementId}/unlock`, {
    method: 'POST',
    body: JSON.stringify({ password }),
    timeoutMs: 90000,
  });
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

