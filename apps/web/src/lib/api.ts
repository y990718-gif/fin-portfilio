// 백엔드(apps/api) 응답 형태와 호출 함수. 필드를 바꾸면 apps/api/src/morning_brief/pipeline.py 와 맞춘다.
import { useEffect, useRef, useState } from "react";

export type QuoteGroup = "증시" | "환율" | "금리·원자재";

export interface Quote {
  group: QuoteGroup;
  name: string;
  ticker: string;
  price: number;
  prev: number;
  change: number;
  change_pct: number;
  trade_date: string;
  digits: number;
}

export interface NewsItem {
  title: string;
  summary: string;
  bank_view: string;
  source: string;
  link: string;
}

export interface BriefingContent {
  summary: string[];
  stocks: string[];
  fx: string[];
  rates_commodities: string[];
  top_news: NewsItem[];
  bank_issues: string[];
  term: { term: string; explanation: string };
  interview: { question: string; answer_points: string[] };
}

export interface Briefing {
  date: string;
  date_label: string;
  title: string;
  status: "ok" | "fallback";
  content: BriefingContent | null;
  quotes: Quote[];
  headlines: { source: string; title: string; link: string }[];
  model: string | null;
  created_at: string;
}

export interface BriefingSummary {
  date: string;
  title: string;
  status: "ok" | "fallback";
  headline: string | null;
}

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(response.status, body?.detail ?? `요청 실패 (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  latestBriefing: () => request<Briefing>("/api/briefings/latest"),
  briefing: (date: string) => request<Briefing>(`/api/briefings/${date}`),
  briefings: (limit = 60) => request<BriefingSummary[]>(`/api/briefings?limit=${limit}`),
};

type State<T> =
  | { status: "loading" }
  | { status: "error"; error: ApiError | Error }
  | { status: "ready"; data: T };

/** 화면에서 API 를 부를 때 쓰는 훅. key 가 바뀔 때만 다시 불러온다. */
export function useApi<T>(load: () => Promise<T>, key: string): State<T> {
  const [state, setState] = useState<State<T> & { key: string }>({ status: "loading", key });
  // load 는 렌더마다 새로 만들어지므로 최신 것을 ref 에 담아 두고 key 로만 다시 부른다
  const loadRef = useRef(load);
  useEffect(() => {
    loadRef.current = load;
  });

  useEffect(() => {
    let cancelled = false;
    loadRef.current().then(
      (data) => !cancelled && setState({ status: "ready", data, key }),
      (error: Error) => !cancelled && setState({ status: "error", error, key }),
    );
    return () => {
      cancelled = true;
    };
  }, [key]);

  return state.key === key ? state : { status: "loading" };
}
