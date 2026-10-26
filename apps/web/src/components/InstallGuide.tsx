/** 아이폰 Safari 에서 홈 화면에 추가하는 방법. 추가해야 아침 알림을 받을 수 있다. */
export function InstallGuide() {
  return (
    <section className="card notice">
      <h2>📲 홈 화면에 추가하면 아침 알림을 받을 수 있어요</h2>
      <ol className="steps">
        <li>
          Safari 아래쪽의 <strong>공유 버튼</strong>(네모에서 화살표가 나온 모양)을 눌러요.
        </li>
        <li>
          <strong>홈 화면에 추가</strong>를 눌러요.
        </li>
        <li>홈 화면에 생긴 아이콘으로 앱을 열고, 설정 탭에서 알림을 켜요.</li>
      </ol>
    </section>
  );
}
