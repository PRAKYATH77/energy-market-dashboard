"""
Pulls historical crude oil futures prices (WTI and Brent) and loads them
into a local SQLite database for the energy market dashboard.
"""
import sqlite3

import pandas as pd
import yfinance as yf

from config import DB_PATH

TICKERS = {
    "WTI": "CL=F",
    "Brent": "BZ=F",
}


def fetch_prices(ticker: str, period: str = "5y") -> pd.DataFrame:
    df = yf.Ticker(ticker).history(period=period, interval="1d")
    df = df.reset_index()[["Date", "Close"]]
    df.columns = ["date", "price"]
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df = df.dropna(subset=["price"])
    return df


def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS oil_prices")

    for name, ticker in TICKERS.items():
        print(f"Fetching {name} ({ticker})...")
        df = fetch_prices(ticker)
        df["benchmark"] = name
        df.to_sql("oil_prices", conn, if_exists="append", index=False)
        print(f"  loaded {len(df)} rows")

    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_benchmark_date ON oil_prices(benchmark, date)"
    )
    conn.commit()
    conn.close()
    print(f"Done. Database at {DB_PATH}")


if __name__ == "__main__":
    main()
