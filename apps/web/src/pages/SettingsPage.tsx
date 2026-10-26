import { useEffect, useState } from "react";

import { InstallGuide } from "../components/InstallGuide";
import {
  currentSubscription,
  disablePush,
  enablePush,
  pushSupport,
  sendTestPush,
} from "../lib/push";

const TEST_RESULT: Record<string, string> = {
  sent: "시험 알림을 보냈어요. 몇 초 안에 도착해요.",
  gone: "이 기기의 알림 등록이 끊겼어요. 알림을 다시 켜 주세요.",
  failed: "알림을 보내지 못했어요. 잠시 후 다시 시도해 주세요.",
};

export function SettingsPage() {
  const support = pushSupport();
  const [subscription, setSubscription] = useState<PushSubscription | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    currentSubscription().then(setSubscription, () => setSubscription(null));
  }, []);

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setMessage(null);
    try {
      await action();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "문제가 생겼어요.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <header className="page-header">
        <h1>설정</h1>
      </header>

      {support === "needs-install" && <InstallGuide />}

      <section className="card">
        <h2>🔔 아침 알림</h2>
        {support === "unsupported" && (
          <p className="muted">
            이 브라우저는 알림을 지원하지 않아요. 아이폰은 Safari 에서 열어 주세요.
          </p>
        )}
        {support === "supported" && (
          <>
            <p className="muted">평일 아침 브리핑이 만들어지면 알림으로 알려 드려요.</p>
            {subscription ? (
              <div className="actions">
                <button
                  type="button"
                  disabled={busy}
                  onClick={() =>
                    run(async () => setMessage(TEST_RESULT[await sendTestPush(subscription)]))
                  }
                >
                  시험 알림 보내기
                </button>
                <button
                  type="button"
                  className="secondary"
                  disabled={busy}
                  onClick={() =>
                    run(async () => {
                      await disablePush(subscription);
                      setSubscription(null);
                      setMessage("알림을 껐어요.");
                    })
                  }
                >
                  알림 끄기
                </button>
              </div>
            ) : (
              <div className="actions">
                <button
                  type="button"
                  disabled={busy}
                  onClick={() =>
                    run(async () => {
                      setSubscription(await enablePush());
                      setMessage("알림을 켰어요. 시험 알림으로 확인해 보세요.");
                    })
                  }
                >
                  알림 켜기
                </button>
              </div>
            )}
          </>
        )}
        {message && <p className="message">{message}</p>}
      </section>
    </>
  );
}
