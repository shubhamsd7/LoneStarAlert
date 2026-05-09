export type WatchType = "name" | "address";
export type County = "Harris" | "Travis" | "Dallas" | "Bexar";
export type Urgency = "CRITICAL" | "URGENT" | "WARNING" | "MONITOR";

export interface WatchEntry {
  id: string;
  type: WatchType;
  value: string;
  county: County;
  email: string;
  userEmail: string;
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

type ApiWatchEntry = {
  id: string;
  type: WatchType;
  value: string;
  county: County;
  email?: string;
  user_email?: string;
  createdAt?: string;
  created_at?: string;
};

type ApiCaseAlert = Partial<CaseAlert> & {
  case_id?: string;
  watch_id?: string;
  case_number?: string;
  filing_date?: string;
  deadline_date?: string | null;
  days_remaining?: number | null;
  urgency_level?: string;
  amount_claimed?: number | string | null;
  is_time_barred?: boolean | null;
  limitations_status?: string;
  collector_win_rate?: number | null;
  default_risk_score?: number | null;
  risk_confidence?: number | null;
  miro_board_url?: string;
  answer_text?: string;
  answer_form_url?: string | null;
  legal_aid?: LegalAidResource[];
  message?: string;
  sent_at?: string;
};

type AlertResponse = CaseAlert[] | { alerts?: ApiCaseAlert[]; cases?: ApiCaseAlert[]; data?: ApiCaseAlert[] };

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

function toWatchEntry(watch: ApiWatchEntry): WatchEntry {
  const email = watch.email ?? watch.user_email ?? "";

  return {
    id: watch.id,
    type: watch.type,
    value: watch.value,
    county: watch.county,
    email,
    userEmail: email,
    createdAt: watch.createdAt ?? watch.created_at ?? new Date().toISOString(),
  };
}

function normalizeUrgency(value: unknown, daysRemaining: number | null): Urgency {
  if (value === "CRITICAL" || value === "URGENT" || value === "WARNING" || value === "MONITOR") {
    return value;
  }

  if (daysRemaining == null) return "MONITOR";
  if (daysRemaining <= 3) return "CRITICAL";
  if (daysRemaining <= 7) return "URGENT";
  if (daysRemaining <= 14) return "WARNING";
  return "MONITOR";
}

function toNumber(value: unknown): number | null {
  if (value == null || value === "") return null;
  const numberValue = Number(value);
  return Number.isFinite(numberValue) ? numberValue : null;
}

function toCaseAlert(alert: ApiCaseAlert): CaseAlert {
  const daysRemaining = alert.daysRemaining ?? alert.days_remaining ?? null;
  const isTimeBarred = alert.is_time_barred;
  const limitationsStatus =
    alert.limitationsStatus ??
    alert.limitations_status ??
    (isTimeBarred === true
      ? "Possible statute of limitations defense flagged."
      : isTimeBarred === false
        ? "No limitations flag from available dates."
        : undefined);
  const fallbackId =
    typeof globalThis.crypto?.randomUUID === "function"
      ? globalThis.crypto.randomUUID()
      : `alert-${Date.now()}`;

  return {
    id: String(alert.id ?? alert.caseNumber ?? alert.case_number ?? fallbackId),
    watchId: String(alert.watchId ?? alert.watch_id ?? alert.case_id ?? ""),
    caseNumber: String(alert.caseNumber ?? alert.case_number ?? "Case number pending"),
    filingDate: String(alert.filingDate ?? alert.filing_date ?? ""),
    plaintiff: String(alert.plaintiff ?? "Plaintiff not listed"),
    defendant: alert.defendant,
    county: (alert.county ?? "Harris") as County,
    amount: alert.amount ?? toNumber(alert.amount_claimed),
    deadlineDate: alert.deadlineDate ?? alert.deadline_date ?? null,
    daysRemaining,
    urgency: normalizeUrgency(alert.urgency ?? alert.urgency_level, daysRemaining),
    limitationsStatus,
    collectorWinRate: alert.collectorWinRate ?? alert.collector_win_rate ?? null,
    defaultRiskScore: alert.defaultRiskScore ?? alert.default_risk_score ?? null,
    riskConfidence: alert.riskConfidence ?? alert.risk_confidence ?? null,
    pattern: alert.pattern ?? null,
    answerText: alert.answerText ?? alert.answer_text ?? alert.message,
    miroBoardUrl: alert.miroBoardUrl ?? alert.miro_board_url,
    legalAid: alert.legalAid ?? alert.legal_aid,
  };
}

function unwrapAlerts(response: AlertResponse): ApiCaseAlert[] {
  if (Array.isArray(response)) return response;
  return response.alerts ?? response.cases ?? response.data ?? [];
}

export async function createWatch(
  type: WatchType,
  value: string,
  county: County,
  email: string,
): Promise<WatchEntry> {
  const watch = await request<ApiWatchEntry>("/watch", {
    method: "POST",
    body: JSON.stringify({ type, value, county, email, user_email: email }),
  });

  return toWatchEntry(watch);
}

export async function getAlerts(email: string): Promise<CaseAlert[]> {
  const response = await request<AlertResponse>(`/alerts/${encodeURIComponent(email)}`);
  return unwrapAlerts(response).map(toCaseAlert);
}

export async function checkNow(watchId: string): Promise<CaseAlert[]> {
  const response = await request<AlertResponse>(`/check-now/${encodeURIComponent(watchId)}`, {
    method: "POST",
  });

  return unwrapAlerts(response).map(toCaseAlert);
}

export async function deleteWatch(watchId: string): Promise<void> {
  await request<void>(`/watch/${encodeURIComponent(watchId)}`, { method: "DELETE" });
}
