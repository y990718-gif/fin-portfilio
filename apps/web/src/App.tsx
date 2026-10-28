import { BrowserRouter, NavLink, Route, Routes } from "react-router";

import { BriefingPage } from "./pages/BriefingPage";
import { HistoryPage } from "./pages/HistoryPage";
import { SettingsPage } from "./pages/SettingsPage";
import { TodayPage } from "./pages/TodayPage";

const TABS = [
  { to: "/", label: "오늘", icon: "☀️" },
  { to: "/briefings", label: "지난 브리핑", icon: "🗂️" },
  { to: "/settings", label: "설정", icon: "⚙️" },
];

export function App() {
  return (
    <BrowserRouter>
      <main className="page">
        <Routes>
          <Route path="/" element={<TodayPage />} />
          <Route path="/briefings" element={<HistoryPage />} />
          <Route path="/briefings/:date" element={<BriefingPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<TodayPage />} />
        </Routes>
      </main>
      <nav className="tab-bar" aria-label="주요 메뉴">
        {TABS.map((tab) => (
          <NavLink key={tab.to} to={tab.to} end={tab.to === "/"} className="tab">
            <span aria-hidden="true">{tab.icon}</span>
            {tab.label}
          </NavLink>
        ))}
      </nav>
    </BrowserRouter>
  );
}
