import { apiFetch } from './client';

export interface ReviewQueueItem {
  id: string;
  statement_id: string;
  transaction_id?: string;
  issue_type: string;
  confidence: number;
  suggested_value?: any;
  status: string;
  narration_raw?: string;
  source_page_no?: number;
  amount?: number;
  date?: string;
  created_at: string;
}

export function getReviewQueue(applicationId: string): Promise<ReviewQueueItem[]> {
  return apiFetch<ReviewQueueItem[]>(`/api/applications/${applicationId}/review-queue`);
}

export function resolveReviewItem(
  reviewId: string,
  action: 'APPROVED' | 'REJECTED' | 'CORRECTED',
  reason: string,
  correctedValue?: any
): Promise<any> {
  return apiFetch<any>(`/api/review/${reviewId}/resolve`, {
    method: 'POST',
    body: JSON.stringify({
      action,
      reason,
      corrected_value: correctedValue,
    }),
  });
}

