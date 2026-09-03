"""
Forecasts the next 30 days of crude oil prices per benchmark using a simple
ARIMA time-series model, and writes the forecast back into SQLite.
"""
import sqlite3
import warnings

import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

from config import DB_PATH

warnings.filterwarnings("ignore")

HORIZON_DAYS = 30


def forecast_benchmark(prices: pd.Series, horizon: int = HORIZON_DAYS) -> pd.Series:
    model = ARIMA(prices, order=(5, 1, 0))
    fitted = model.fit()
    return fitted.forecast(steps=horizon)


def main():
    conn = sqlite3.connect(DB_PATH)
    history = pd.read_sql("SELECT * FROM oil_prices ORDER BY date", conn)
    conn.execute("DROP TABLE IF EXISTS oil_price_forecast")

    for benchmark, group in history.groupby("benchmark"):
        group = group.sort_values("date")
        series = group["price"].reset_index(drop=True)
        last_date = pd.to_datetime(group["date"].iloc[-1])

        preds = forecast_benchmark(series)
        future_dates = pd.bdate_range(
            start=last_date + pd.Timedelta(days=1), periods=HORIZON_DAYS
        )

        out = pd.DataFrame(
            {
                "date": future_dates.strftime("%Y-%m-%d"),
                "predicted_price": preds.values,
                "benchmark": benchmark,
            }
        )
        out.to_sql("oil_price_forecast", conn, if_exists="append", index=False)
        print(f"{benchmark}: forecasted {len(out)} days ahead")

    conn.commit()
    conn.close()
    print("Forecast written to oil_price_forecast table.")


if __name__ == "__main__":
    main()
