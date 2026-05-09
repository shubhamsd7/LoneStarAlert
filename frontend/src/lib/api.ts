export type WatchType = "name" | "address";
export type County = "Harris" | "Travis" | "Dallas" | "Bexar";
export type Urgency = "CRITICAL" | "URGENT" | "WARNING" | "MONITOR";

export interface WatchEntry {
  id: string;
  type: WatchType;
  value: string;
  county: County;
  email: string;
  createdAt: string;
}

export interface PatternSignal {
  severity: "low" | "medium" | "high";
  description: string;
  anomalyScore?: number;
}

export interface LegalAidResource {
  name: string;
  phone?: string;
  url?: string;
}

export interface CaseAlert {
  id: string;
  watchId: string;
  caseNumber: string;
  filingDate: string;
  plaintiff: string;
  defendant?: string;
  county: County;
  amount: number | null;
  deadlineDate: string | null;
  daysRemaining: number | null;
  urgency: Urgency;
  limitationsStatus?: string;
  collectorWinRate?: number | null;
  defaultRiskScore?: number | null;
  riskConfidence?: number | null;
  pattern?: PatternSignal | null;
  answerText?: string;
  miroBoardUrl?: string;
  legalAid?: LegalAidResource[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `TxAlert API failed with ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export async function createWatch(
  type: WatchType,
  value: string,
  county: County,
  email: string,
): Promise<WatchEntry> {
  return request<WatchEntry>("/watches", {
    method: "POST",
    body: JSON.stringify({ type, value, county, email, user_email: email }),
  });
}

export async function getAlerts(email: string): Promise<CaseAlert[]> {
  const params = new URLSearchParams({ email });
  return request<CaseAlert[]>(`/alerts?${params.toString()}`);
}

export async function checkNow(watchId: string): Promise<CaseAlert[]> {
  return request<CaseAlert[]>(`/watches/${watchId}/check`, { method: "POST" });
}

export async function deleteWatch(watchId: string): Promise<void> {
  await request<void>(`/watches/${watchId}`, { method: "DELETE" });
}
