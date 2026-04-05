/**
 * Centralized API Service
 * All backend calls go through this module.
 * The base URL is read from VITE_API_URL environment variable.
 *
 * Development:  VITE_API_URL=http://localhost:5000  (or use Vite proxy at /api)
 * Production:   VITE_API_URL=https://your-api.onrender.com
 */

const API_BASE = import.meta.env.VITE_API_URL ?? '';

// Using the Vite proxy in dev means API_BASE can be '' and /api still routes correctly.
const API = `${API_BASE}/api`;

// ─── Types ────────────────────────────────────────────────────────────────────

export type SystemStatus = 'stopped' | 'starting' | 'running';

export interface StatusResponse {
  status: SystemStatus;
  mode: number | null;
  mode_name?: string;
  running: boolean;
}

export interface ApiResult {
  status: 'success' | 'error' | 'info' | 'starting';
  message?: string;
  mode?: number;
}

export interface User {
  username: string;
  user_id: string;
  enrolled_date: string | null;
}

export interface Signature {
  id: number;
  filename: string;
  url: string;
  public_id: string;
  point_count: number;
  created_at: string | null;
  username: string | null;
}

export interface AuthStatus {
  auth_mode: 'NONE' | 'ENROLL' | 'VERIFY';
  auth_username: string | null;
  trajectory_points: number;
  has_result: boolean;
  result?: Record<string, unknown>;
}

export interface Thresholds {
  dtw_threshold: number;
  feature_threshold: number;
  min_signature_points: number;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.message ?? `Request failed with status ${res.status}`);
  }

  return data as T;
}

// ─── System Control ───────────────────────────────────────────────────────────

/** Start the HCI system */
export const startSystem = () =>
  apiFetch<ApiResult>('/start', { method: 'POST' });

/** Stop the HCI system */
export const stopSystem = () =>
  apiFetch<ApiResult>('/stop', { method: 'POST' });

/** Get current system status (used for polling) */
export const getStatus = () =>
  apiFetch<StatusResponse>('/status');

/** Switch interaction mode: 0=Standby, 1=VirtualMouse, 2=Facial, 3=AirSignature */
export const setMode = (mode: 0 | 1 | 2 | 3) =>
  apiFetch<ApiResult>(`/mode/${mode}`, { method: 'POST' });

// ─── Signatures ───────────────────────────────────────────────────────────────

/** List all saved signatures (Cloudinary URLs from PostgreSQL) */
export const listSignatures = () =>
  apiFetch<{ status: string; signatures: Signature[]; count: number }>('/signatures');

// ─── Auth — Users ─────────────────────────────────────────────────────────────

/** List all enrolled users */
export const listUsers = () =>
  apiFetch<{ status: string; users: User[]; count: number }>('/auth/users');

/** Start enrollment for a username */
export const enrollUser = (username: string) =>
  apiFetch<ApiResult>('/auth/enroll', {
    method: 'POST',
    body: JSON.stringify({ username }),
  });

/** Start verification for a username */
export const verifyUser = (username: string) =>
  apiFetch<ApiResult>('/auth/verify', {
    method: 'POST',
    body: JSON.stringify({ username }),
  });

/** Cancel current auth operation */
export const cancelAuth = () =>
  apiFetch<ApiResult>('/auth/cancel', { method: 'POST' });

/** Delete an enrolled user */
export const deleteUser = (username: string) =>
  apiFetch<ApiResult>(`/auth/delete/${encodeURIComponent(username)}`, {
    method: 'DELETE',
  });

// ─── Auth — Status & Config ───────────────────────────────────────────────────

/** Poll current authentication operation status */
export const getAuthStatus = () =>
  apiFetch<{ status: string; auth_status: AuthStatus }>('/auth/status');

/** Get current DTW / feature thresholds */
export const getThresholds = () =>
  apiFetch<{ status: string; thresholds: Thresholds }>('/auth/thresholds');

/** Update authentication thresholds */
export const updateThresholds = (dtw_threshold?: number, feature_threshold?: number) =>
  apiFetch<{ status: string; thresholds: Thresholds }>('/auth/thresholds', {
    method: 'POST',
    body: JSON.stringify({ dtw_threshold, feature_threshold }),
  });
