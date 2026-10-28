import type { Quote } from "./api";

/** 한국 증시 관례대로 상승은 빨강(up), 하락은 파랑(down). */
export function direction(change: number): "up" | "down" | "flat" {
  if (change > 0) return "up";
  if (change < 0) return "down";
  return "flat";
}

export function formatNumber(value: number, digits: number): string {
  return value.toLocaleString("ko-KR", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function formatChange(quote: Quote): string {
  const arrow = { up: "▲", down: "▼", flat: "–" }[direction(quote.change)];
  const pct = `${quote.change_pct >= 0 ? "+" : ""}${quote.change_pct.toFixed(2)}%`;
  return `${arrow}${formatNumber(Math.abs(quote.change), quote.digits)} (${pct})`;
}

/** "2026-10-27" → "10월 27일 (화)" */
export function shortDate(date: string): string {
  const [year, month, day] = date.split("-").map(Number);
  const weekday = "일월화수목금토"[new Date(year, month - 1, day).getDay()];
  return `${month}월 ${day}일 (${weekday})`;
}
