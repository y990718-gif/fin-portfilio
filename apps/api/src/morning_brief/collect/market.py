"""증시·환율·금리·원자재 시세 수집 (Yahoo Finance, yfinance)."""

from __future__ import annotations

from dataclasses import dataclass

import yfinance as yf

# (그룹, 표시 이름, 야후 파이낸스 티커, 소수점 자릿수)
TICKERS = [
    ("증시", "코스피", "^KS11", 2),
    ("증시", "코스닥", "^KQ11", 2),
    ("증시", "S&P 500", "^GSPC", 2),
    ("증시", "나스닥", "^IXIC", 2),
    ("증시", "다우존스", "^DJI", 2),
    ("증시", "닛케이 225", "^N225", 2),
    ("증시", "상하이종합", "000001.SS", 2),
    ("환율", "원/달러", "KRW=X", 2),
    ("환율", "원/100엔", "JPYKRW=X", 2),  # 아래에서 100을 곱함
    ("환율", "원/유로", "EURKRW=X", 2),
    ("환율", "원/위안", "KRWCNY=X", 2),  # 위안/원 값을 뒤집어 씀
    ("환율", "달러인덱스", "DX-Y.NYB", 2),
    ("금리·원자재", "미 국채 10년(%)", "^TNX", 3),
    ("금리·원자재", "WTI 유가($)", "CL=F", 2),
    ("금리·원자재", "금($/oz)", "GC=F", 1),
]


@dataclass
class Quote:
    group: str
    name: str
    ticker: str
    price: float
    prev: float
    date: str  # 마지막 거래일 (YYYY-MM-DD)
    digits: int

    @property
    def change(self) -> float:
        return self.price - self.prev

    @property
    def change_pct(self) -> float:
        return self.change / self.prev * 100 if self.prev else 0.0

    def fmt(self, value: float) -> str:
        return f"{value:,.{self.digits}f}"

    def line(self) -> str:
        arrow = "▲" if self.change > 0 else "▼" if self.change < 0 else "–"
        return (
            f"{self.name}: {self.fmt(self.price)} "
            f"({arrow}{self.fmt(abs(self.change))}, {self.change_pct:+.2f}%) [{self.date}]"
        )

    def to_doc(self) -> dict:
        """MongoDB 와 API 응답에 쓰는 형태."""
        return {
            "group": self.group,
            "name": self.name,
            "ticker": self.ticker,
            "price": self.price,
            "prev": self.prev,
            "change": self.change,
            "change_pct": self.change_pct,
            "trade_date": self.date,
            "digits": self.digits,
        }


def fetch_quotes() -> list[Quote]:
    quotes = []
    for group, name, ticker, digits in TICKERS:
        try:
            hist = yf.Ticker(ticker).history(period="10d", auto_adjust=False)
            closes = hist["Close"].dropna()
            if len(closes) < 2:
                print(f"[market] {ticker}: 데이터 부족, 건너뜀")
                continue
            price, prev = float(closes.iloc[-1]), float(closes.iloc[-2])
            if ticker == "JPYKRW=X":
                price, prev = price * 100, prev * 100
            elif ticker == "KRWCNY=X":
                price, prev = 1 / price, 1 / prev
            quotes.append(
                Quote(group, name, ticker, price, prev, closes.index[-1].strftime("%Y-%m-%d"), digits)
            )
        except Exception as e:  # 한 종목 실패가 전체 보고서를 막지 않도록
            print(f"[market] {ticker} 실패: {e}")
    return quotes
