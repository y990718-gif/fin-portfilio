// 아침 알림(웹 푸시). 아이폰은 Safari 에서 "홈 화면에 추가"한 앱으로 열었을 때만 알림을 받을 수 있다.
import { request } from "./api";

export type PushSupport =
  | "supported"
  | "needs-install" // 아이폰 Safari 에서 아직 홈 화면에 추가하지 않음
  | "unsupported";

export function isStandalone(): boolean {
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    (navigator as Navigator & { standalone?: boolean }).standalone === true
  );
}

export function isIos(): boolean {
  return /iPhone|iPad|iPod/.test(navigator.userAgent);
}

export function pushSupport(): PushSupport {
  const capable =
    "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
  if (capable && (!isIos() || isStandalone())) return "supported";
  if (isIos() && !isStandalone()) return "needs-install";
  return "unsupported";
}

export function registerServiceWorker(): void {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js").catch((error) => {
      console.error("서비스 워커 등록 실패", error);
    });
  }
}

async function registration(): Promise<ServiceWorkerRegistration> {
  return navigator.serviceWorker.ready;
}

export async function currentSubscription(): Promise<PushSubscription | null> {
  if (pushSupport() !== "supported") return null;
  return (await registration()).pushManager.getSubscription();
}

function base64UrlToBytes(value: string): Uint8Array<ArrayBuffer> {
  const padded = (value + "=".repeat((4 - (value.length % 4)) % 4))
    .replace(/-/g, "+")
    .replace(/_/g, "/");
  const binary = atob(padded);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

/** 버튼을 눌렀을 때만 부른다. 아이폰은 사용자가 누른 순간에만 알림 권한을 물어볼 수 있다. */
export async function enablePush(): Promise<PushSubscription> {
  const permission = await Notification.requestPermission();
  if (permission !== "granted") {
    throw new Error("알림이 허용되지 않았어요. 설정 앱 → 알림에서 이 앱을 허용해 주세요.");
  }
  const { public_key } = await request<{ public_key: string }>("/api/push/public-key");
  const reg = await registration();
  const subscription =
    (await reg.pushManager.getSubscription()) ??
    (await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: base64UrlToBytes(public_key),
    }));
  await request("/api/push/subscriptions", {
    method: "POST",
    body: JSON.stringify(subscription.toJSON()),
  });
  return subscription;
}

export async function disablePush(subscription: PushSubscription): Promise<void> {
  await request("/api/push/unsubscribe", {
    method: "POST",
    body: JSON.stringify({ endpoint: subscription.endpoint }),
  });
  await subscription.unsubscribe();
}

export async function sendTestPush(subscription: PushSubscription): Promise<string> {
  const { result } = await request<{ result: string }>("/api/push/test", {
    method: "POST",
    body: JSON.stringify({ endpoint: subscription.endpoint }),
  });
  return result;
}
