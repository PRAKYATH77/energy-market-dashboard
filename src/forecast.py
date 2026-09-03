"""
Forecasts the next 30 days of crude oil prices per benchmark using ARIMA.

Before fitting on the full series, each benchmark is:
1. Tested for stationarity (Augmented Dickey-Fuller) to justify the
   differencing order rather than assuming it.
2. Backtested on a held-out 30-day window so forecast accuracy (MAE,
   RMSE, MAPE) is measured against real outcomes, not just projected
   blindly into the future.
"""
import sqlite3
import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller

from config import DB_PATH

warnings.filterwarnings("ignore")

HORIZON_DAYS = 30


def is_stationary(series: pd.Series, alpha: float = 0.05) -> bool:
    p_value = adfuller(series.dropna())[1]
    return p_value < alpha


def fit_arima(prices: pd.Series, horizon: int) -> pd.Series:
    order = (5, 1, 0) if not is_stationary(prices) else (5, 0, 0)
    model = ARIMA(prices, order=order)
    return model.fit().forecast(steps=horizon)


def backtest(series: pd.Series, holdout: int = HORIZON_DAYS) -> dict:
    train, test = series[:-holdout], series[-holdout:]
    preds = fit_arima(train, horizon=holdout)
    preds = pd.Series(preds.values, index=test.index)

    mae = float(np.mean(np.abs(test - preds)))
    rmse = float(np.sqrt(np.mean((test - preds) ** 2)))
    mape = float(np.mean(np.abs((test - preds) / test)) * 100)
    return {"mae": mae, "rmse": rmse, "mape": mape}


def main():
    conn = sqlite3.connect(DB_PATH)
    history = pd.read_sql("SELECT * FROM oil_prices ORDER BY date", conn)
    conn.execute("DROP TABLE IF EXISTS oil_price_forecast")
    conn.execute("DROP TABLE IF EXISTS oil_price_backtest")

    for benchmark, group in history.groupby("benchmark"):
        group = group.sort_values("date")
        series = group["price"].reset_index(drop=True)
        last_date = pd.to_datetime(group["date"].iloc[-1])

        metrics = backtest(series)
        metrics["benchmark"] = benchmark
        pd.DataFrame([metrics]).to_sql(
            "oil_price_backtest", conn, if_exists="append", index=False
        )
        print(
            f"{benchmark} backtest (last {HORIZON_DAYS}d held out): "
            f"MAE={metrics['mae']:.2f} RMSE={metrics['rmse']:.2f} "
            f"MAPE={metrics['mape']:.2f}%"
        )

        preds = fit_arima(series, horizon=HORIZON_DAYS)
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
    print("Forecast and backtest metrics written to SQLite.")


if __name__ == "__main__":
    main()
