import type { ReactNode } from "react";

import type { Briefing } from "../lib/api";
import { QuoteBoard } from "./QuoteBoard";

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="card">
      <h2>{title}</h2>
      {children}
    </section>
  );
}

function Lines({ lines }: { lines: string[] }) {
  return (
    <ul className="lines">
      {lines.map((line) => (
        <li key={line}>{line}</li>
      ))}
    </ul>
  );
}

export function BriefingView({ briefing }: { briefing: Briefing }) {
  const content = briefing.content;
  return (
    <article className="briefing">
      <header className="briefing-header">
        <p className="eyebrow">아침 경제 브리핑</p>
        <h1>{briefing.date_label}</h1>
      </header>

      {content ? (
        <>
          <section className="card highlight">
            <h2>🧭 오늘의 3줄 요약</h2>
            <ol className="summary">
              {content.summary.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ol>
          </section>

          <Section title="📊 오늘의 시세">
            <QuoteBoard quotes={briefing.quotes} />
          </Section>
          <Section title="💱 환율">
            <Lines lines={content.fx} />
          </Section>
          <Section title="📈 증시">
            <Lines lines={content.stocks} />
          </Section>
          <Section title="🏦 금리·원자재">
            <Lines lines={content.rates_commodities} />
          </Section>

          <Section title="📰 주요 뉴스">
            <ol className="news">
              {content.top_news.map((news) => (
                <li key={news.link}>
                  <h3>{news.title}</h3>
                  <p>{news.summary}</p>
                  <p className="bank-view">
                    <strong>은행원 관점</strong> {news.bank_view}
                  </p>
                  <a href={news.link} target="_blank" rel="noreferrer">
                    원문 보기 · {news.source}
                  </a>
                </li>
              ))}
            </ol>
          </Section>

          <Section title="🏛️ 은행·금융권 이슈">
            <Lines lines={content.bank_issues} />
          </Section>
          <Section title="📚 오늘의 경제 용어">
            <p>
              <strong>{content.term.term}</strong> — {content.term.explanation}
            </p>
          </Section>
          <Section title="🎤 면접 대비 한 문장">
            <p className="question">Q. {content.interview.question}</p>
            <Lines lines={content.interview.answer_points} />
          </Section>
        </>
      ) : (
        <>
          <section className="card notice">
            <h2>⚠️ AI 요약 없이 원자료만 보여 드려요</h2>
            <p className="muted">오늘은 요약을 만들지 못했어요. 헤드라인과 시세만 확인해 주세요.</p>
          </section>
          <Section title="📊 오늘의 시세">
            <QuoteBoard quotes={briefing.quotes} />
          </Section>
          <Section title="📰 헤드라인">
            <ul className="headlines">
              {briefing.headlines.map((h) => (
                <li key={h.link}>
                  <a href={h.link} target="_blank" rel="noreferrer">
                    {h.title}
                  </a>
                  <span className="muted small"> · {h.source}</span>
                </li>
              ))}
            </ul>
          </Section>
        </>
      )}
    </article>
  );
}
