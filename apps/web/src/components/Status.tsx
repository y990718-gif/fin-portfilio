import { ApiError } from "../lib/api";

export function Loading() {
  return <p className="status muted">불러오는 중…</p>;
}

export function ErrorMessage({ error, emptyText }: { error: Error; emptyText?: string }) {
  if (error instanceof ApiError && error.status === 404 && emptyText) {
    return <p className="status muted">{emptyText}</p>;
  }
  return (
    <p className="status error">{error.message || "문제가 생겼어요. 잠시 후 다시 열어 주세요."}</p>
  );
}
