import type { Quote, QuoteGroup } from "../lib/api";
import { direction, formatChange, formatNumber } from "../lib/format";

const GROUPS: QuoteGroup[] = ["환율", "증시", "금리·원자재"];

export function QuoteBoard({ quotes }: { quotes: Quote[] }) {
  if (quotes.length === 0) {
    return <p className="muted">시세를 가져오지 못했어요.</p>;
  }
  return (
    <div className="quote-board">
      {GROUPS.map((group) => {
        const rows = quotes.filter((q) => q.group === group);
        if (rows.length === 0) return null;
        return (
          <div key={group} className="quote-group">
            <h3>{group}</h3>
            <ul>
              {rows.map((q) => (
                <li key={q.ticker} className="quote-row">
                  <span className="quote-name">{q.name}</span>
                  <span className="quote-price">{formatNumber(q.price, q.digits)}</span>
                  <span className={`quote-change ${direction(q.change)}`}>{formatChange(q)}</span>
                </li>
              ))}
            </ul>
          </div>
        );
      })}
      <p className="muted small">
        마지막 거래일 기준 · Yahoo Finance (은행 고시 환율과 조금 다를 수 있어요)
      </p>
    </div>
  );
}
