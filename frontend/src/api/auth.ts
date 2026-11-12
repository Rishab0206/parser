import { apiFetch } from './client';

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  role: 'Admin' | 'Staff';
  is_active?: boolean;
  customers_count?: number;
  created_at?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

export interface InviteItem {
  id: string;
  token: string;
  email: string;
  name: string;
  role: string;
  status: 'PENDING' | 'ACCEPTED' | 'EXPIRED';
  is_used: boolean;
  expires_at: string;
  created_at: string;
}

export function loginApi(email: string, password: string): Promise<LoginResponse> {
  return apiFetch<LoginResponse>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export function getMeApi(): Promise<UserProfile> {
  return apiFetch<UserProfile>('/api/auth/me');
}

export function createInviteApi(name: string, email: string): Promise<any> {
  return apiFetch<any>('/api/admin/invites', {
    method: 'POST',
    body: JSON.stringify({ name, email, role: 'Staff' }),
  });
}

export function listInvitesApi(): Promise<InviteItem[]> {
  return apiFetch<InviteItem[]>('/api/admin/invites');
}

export function listUsersApi(): Promise<UserProfile[]> {
  return apiFetch<UserProfile[]>('/api/admin/users');
}

export function deleteUserApi(userId: string): Promise<any> {
  return apiFetch<any>(`/api/admin/users/${userId}`, {
    method: 'DELETE',
  });
}

export function getInviteDetailsApi(token: string): Promise<{ email: string; name: string; role: string; expires_at: string }> {
  return apiFetch<{ email: string; name: string; role: string; expires_at: string }>(`/api/auth/invite/${token}`);
}

export function acceptInviteApi(token: string, password: string): Promise<LoginResponse> {
  return apiFetch<LoginResponse>('/api/auth/accept-invite', {
    method: 'POST',
    body: JSON.stringify({ token, password }),
  });
}
