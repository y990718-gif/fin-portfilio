import { Link } from "react-router";

import { ErrorMessage, Loading } from "../components/Status";
import { api, useApi } from "../lib/api";
import { shortDate } from "../lib/format";

export function HistoryPage() {
  const state = useApi(() => api.briefings(), "history");
  return (
    <>
      <header className="page-header">
        <h1>지난 브리핑</h1>
      </header>
      {state.status === "loading" && <Loading />}
      {state.status === "error" && <ErrorMessage error={state.error} />}
      {state.status === "ready" &&
        (state.data.length === 0 ? (
          <p className="status muted">아직 쌓인 브리핑이 없어요.</p>
        ) : (
          <ul className="history">
            {state.data.map((item) => (
              <li key={item.date}>
                <Link to={`/briefings/${item.date}`} className="card history-item">
                  <span className="history-date">{shortDate(item.date)}</span>
                  <span className="history-headline">
                    {item.headline ?? "AI 요약 없이 원자료만 있는 날"}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        ))}
    </>
  );
}
