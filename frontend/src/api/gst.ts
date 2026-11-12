import { apiFetch } from './client';

export interface GstinItem {
  gstin: string;
  state_code: string;
  state_name: string;
  entity_number: string;
  checksum_valid: boolean;
  status: string;
  source: string;
}

export interface GstMatchingAnalysis {
  customer_name: string;
  match_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  observations: string[];
  underwriting_recommendation: string;
}

export interface GstLookupResponse {
  valid: boolean;
  input_type: 'PAN' | 'GSTIN';
  input_value: string;
  pan: string;
  entity_code: string;
  entity_type: string;
  name_initial: string;
  gstins: GstinItem[];
  all_states: Record<string, string>;
  gov_search_url: string;
  matching: GstMatchingAnalysis;
}

export function lookupGstOrPan(
  query: string,
  applicationId?: string,
  customerName?: string,
  targetState?: string
): Promise<GstLookupResponse> {
  return apiFetch<GstLookupResponse>('/api/gst/lookup', {
    method: 'POST',
    body: JSON.stringify({
      query: query.trim().toUpperCase(),
      application_id: applicationId || undefined,
      customer_name: customerName || undefined,
      target_state: targetState || undefined,
    }),
  });
}
