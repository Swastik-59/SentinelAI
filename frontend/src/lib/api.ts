/**
 * SentinelAI — API Client
 *
 * Handles all communication with the FastAPI backend.
 * Includes authentication, case management, analytics, and client APIs.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Auth helpers ─────────────────────────────────────────────────────────

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("sentinel_token");
}

function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function apiFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...init,
    headers: { ...authHeaders(), ...init?.headers },
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Types ────────────────────────────────────────────────────────────────

export interface TextAnalysisResult {
  ai_probability: number;
  fraud_probability: number;
  fraud_risk_score: number;
  risk_score: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  highlighted_phrases: string[];
  explanation: string;
  details: string[];
  stylometric_features: Record<string, number>;
  fraud_signals: {
    urgency: { keywords: string[]; score: number; count: number };
    financial_redirection: { keywords: string[]; score: number; count: number };
    impersonation: { keywords: string[]; score: number; count: number };
  };
  case_id?: string | null;
  escalation_reason?: string | null;
}

export interface ImageAnalysisResult {
  deepfake_probability: number;
  fraud_risk_score: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  explanation: string;
  details: string[];
  analysis_method: string;
}

export interface DocumentAnalysisResult {
  ai_probability: number;
  fraud_probability: number;
  fraud_risk_score: number;
  risk_score: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  highlighted_phrases: string[];
  explanation: string;
  details: string[];
  extracted_text_preview: string;
  page_count: number;
  stylometric_features: Record<string, number>;
  fraud_signals: {
    urgency: { keywords: string[]; score: number; count: number };
    financial_redirection: { keywords: string[]; score: number; count: number };
    impersonation: { keywords: string[]; score: number; count: number };
  };
  case_id?: string | null;
  escalation_reason?: string | null;
}

export interface AuditLogEntry {
  id: number;
  timestamp: string;
  input_type: string;
  ai_probability: number;
  fraud_risk_score: number;
  risk_level: string;
  result: Record<string, unknown>;
  flagged: boolean;
}

export interface AuditLogResponse {
  logs: AuditLogEntry[];
  count: number;
}

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  models: { ai_detector: boolean; fraud_detector: boolean; models_loaded: boolean };
  ollama: boolean;
}

// ── Auth Types ───────────────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string;
  token_type: string;
  role: string;
  username: string;
}

export interface UserProfile {
  id: string;
  username: string;
  role: string;
  full_name: string;
  created_at: string;
}

// ── Case Types ───────────────────────────────────────────────────────────

export type CaseStatus = "OPEN" | "UNDER_REVIEW" | "ESCALATED" | "RESOLVED" | "FALSE_POSITIVE";
export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface CaseNote {
  id: number;
  case_id: string;
  author: string;
  note: string;
  timestamp: string;
}

export interface Case {
  id: string;
  content_hash: string | null;
  risk_score: number;
  ai_probability: number;
  fraud_probability: number;
  risk_level: RiskLevel;
  status: CaseStatus;
  assigned_to: string | null;
  escalation_reason: string | null;
  client_id: string | null;
  result: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  notes?: CaseNote[];
}

export interface CaseListResponse {
  cases: Case[];
  count: number;
}

// ── Client Types ─────────────────────────────────────────────────────────

export interface Client {
  id: string;
  name: string;
  industry: string | null;
  contact_email: string | null;
  total_cases: number;
  open_cases: number;
  avg_risk_score: number;
  created_at: string;
}

export interface ClientRiskSummary {
  client: Client;
  risk_distribution: Record<string, number>;
  status_distribution: Record<string, number>;
  recent_cases: Case[];
}

// ── Analytics Types ──────────────────────────────────────────────────────

export interface FraudPerDay {
  date: string;
  count: number;
}

export interface AnalyticsOverview {
  fraud_per_day: FraudPerDay[];
  ai_fraud_percentage: number;
  risk_breakdown: Record<string, number>;
  type_breakdown: Record<string, number>;
  case_status: Record<string, number>;
  avg_resolution_hours: number | null;
  top_fraud_keywords: { keyword: string; count: number }[];
  total_cases: number;
  total_escalated: number;
}

// ── API Functions ────────────────────────────────────────────────────────

// Analysis
export async function analyzeText(text: string): Promise<TextAnalysisResult> {
  return apiFetch(`${API_BASE}/analyze/text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
}

export async function analyzeImage(file: File): Promise<ImageAnalysisResult> {
  const formData = new FormData();
  formData.append("file", file);
  const token = getToken();
  const res = await fetch(`${API_BASE}/analyze/image`, {
    method: "POST",
    body: formData,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function analyzeDocument(file: File): Promise<DocumentAnalysisResult> {
  const formData = new FormData();
  formData.append("file", file);
  const token = getToken();
  const res = await fetch(`${API_BASE}/analyze/document`, {
    method: "POST",
    body: formData,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// Audit
export async function getAuditLogs(params?: {
  limit?: number;
  offset?: number;
  flagged_only?: boolean;
  input_type?: string;
}): Promise<AuditLogResponse> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset) searchParams.set("offset", String(params.offset));
  if (params?.flagged_only) searchParams.set("flagged_only", "true");
  if (params?.input_type) searchParams.set("input_type", params.input_type);
  return apiFetch(`${API_BASE}/audit/logs?${searchParams}`);
}

export async function healthCheck(): Promise<HealthStatus> {
  return apiFetch(`${API_BASE}/health`);
}

// Auth
export async function login(username: string, password: string): Promise<TokenResponse> {
  const data = await apiFetch<TokenResponse>(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  localStorage.setItem("sentinel_token", data.access_token);
  localStorage.setItem("sentinel_user", JSON.stringify({ username: data.username, role: data.role }));
  return data;
}

export async function register(
  username: string,
  password: string,
  role: string = "analyst",
  full_name: string = "",
): Promise<{ user_id: string; message: string }> {
  return apiFetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password, role, full_name }),
  });
}

export async function getMe(): Promise<UserProfile> {
  return apiFetch(`${API_BASE}/auth/me`);
}

export function logout() {
  localStorage.removeItem("sentinel_token");
  localStorage.removeItem("sentinel_user");
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

export function getCurrentUser(): { username: string; role: string } | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("sentinel_user");
  return raw ? JSON.parse(raw) : null;
}

// Cases
export async function getCases(params?: {
  limit?: number;
  offset?: number;
  status?: CaseStatus;
  risk_level?: RiskLevel;
  client_id?: string;
}): Promise<CaseListResponse> {
  const sp = new URLSearchParams();
  if (params?.limit) sp.set("limit", String(params.limit));
  if (params?.offset) sp.set("offset", String(params.offset));
  if (params?.status) sp.set("status", params.status);
  if (params?.risk_level) sp.set("risk_level", params.risk_level);
  if (params?.client_id) sp.set("client_id", params.client_id);
  return apiFetch(`${API_BASE}/cases?${sp}`);
}

export async function getCase(caseId: string): Promise<Case> {
  return apiFetch(`${API_BASE}/cases/${caseId}`);
}

export async function updateCaseStatus(
  caseId: string,
  status: CaseStatus,
  assigned_to?: string,
): Promise<Case> {
  return apiFetch(`${API_BASE}/cases/${caseId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status, assigned_to }),
  });
}

export async function addCaseNote(caseId: string, note: string): Promise<CaseNote> {
  return apiFetch(`${API_BASE}/cases/${caseId}/notes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ note }),
  });
}

export function getCaseExportUrl(caseId: string): string {
  return `${API_BASE}/cases/${caseId}/export`;
}

// Clients
export async function getClients(params?: {
  limit?: number;
  offset?: number;
}): Promise<{ clients: Client[]; count: number }> {
  const sp = new URLSearchParams();
  if (params?.limit) sp.set("limit", String(params.limit));
  if (params?.offset) sp.set("offset", String(params.offset));
  return apiFetch(`${API_BASE}/clients?${sp}`);
}

export async function createClient(
  name: string,
  industry?: string,
  contact_email?: string,
): Promise<Client> {
  return apiFetch(`${API_BASE}/clients`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, industry, contact_email }),
  });
}

export async function getClientRiskSummary(clientId: string): Promise<ClientRiskSummary> {
  return apiFetch(`${API_BASE}/clients/${clientId}/risk-summary`);
}

// Analytics
export async function getAnalyticsOverview(days: number = 30): Promise<AnalyticsOverview> {
  return apiFetch(`${API_BASE}/analytics/overview?days=${days}`);
}
