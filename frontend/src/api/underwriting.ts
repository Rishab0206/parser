import { apiFetch } from './client';

export interface UnderwritingExportResult {
  export_id: string;
  application_id: string;
  analysis_version_id: string;
  payload: any;
  status: string;
  sent_to_engine_at: string;
}

export interface AnalysisVersionItem {
  id: string;
  version_no: number;
  created_by: string;
  created_at: string;
  is_current: boolean;
  summary: any;
}

export function exportToUnderwriting(applicationId: string): Promise<UnderwritingExportResult> {
  return apiFetch<UnderwritingExportResult>('/api/underwriting/export', {
    method: 'POST',
    body: JSON.stringify({ application_id: applicationId }),
  });
}

export function getApplicationHistory(applicationId: string): Promise<AnalysisVersionItem[]> {
  return apiFetch<AnalysisVersionItem[]>(`/api/applications/${applicationId}/history`);
}

