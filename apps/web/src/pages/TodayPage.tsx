import { BriefingView } from "../components/BriefingView";
import { InstallGuide } from "../components/InstallGuide";
import { ErrorMessage, Loading } from "../components/Status";
import { api, useApi } from "../lib/api";
import { pushSupport } from "../lib/push";

export function TodayPage() {
  const state = useApi(api.latestBriefing, "latest");
  return (
    <>
      {pushSupport() === "needs-install" && <InstallGuide />}
      {state.status === "loading" && <Loading />}
      {state.status === "error" && (
        <ErrorMessage
          error={state.error}
          emptyText="아직 만들어진 브리핑이 없어요. 내일 아침에 만나요!"
        />
      )}
      {state.status === "ready" && <BriefingView briefing={state.data} />}
    </>
  );
}
