import { Link, useParams } from "react-router";

import { BriefingView } from "../components/BriefingView";
import { ErrorMessage, Loading } from "../components/Status";
import { api, useApi } from "../lib/api";

export function BriefingPage() {
  const { date = "" } = useParams();
  const state = useApi(() => api.briefing(date), date);
  return (
    <>
      <Link to="/briefings" className="back">
        ← 지난 브리핑
      </Link>
      {state.status === "loading" && <Loading />}
      {state.status === "error" && (
        <ErrorMessage error={state.error} emptyText="이 날짜의 브리핑은 없어요." />
      )}
      {state.status === "ready" && <BriefingView briefing={state.data} />}
    </>
  );
}
