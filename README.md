# Crude Oil Market Intelligence Dashboard

A small end-to-end data pipeline built to mirror the core workflow of an
energy Data & Research Analyst: collect market data, clean and store it,
apply a statistical forecast, and surface the result as a client-facing
dashboard.

## Pipeline

1. **Collect** — `src/fetch_data.py` pulls 5 years of daily WTI and Brent
   crude futures prices via the Yahoo Finance API.
2. **Store** — prices are loaded into a local SQLite database
   (`data/energy_data.db`), indexed by benchmark and date.
3. **Forecast** — `src/forecast.py` fits an ARIMA(5,1,0) time-series model
   per benchmark and projects prices 30 trading days forward.
4. **Deliver** — `src/dashboard.py` is a Streamlit app showing historical
   vs. forecast price charts, 30-day change, realized volatility, and an
   auto-generated one-line market insight — the kind of quick-read output
   a research analyst would hand to a client.

## Why this maps to the role

This project touches the core bullets of an energy Data & Research Analyst
role: collecting and cleaning multi-source data, building a structured SQL
store, applying statistical/forecasting methods in Python, and translating
the output into a clear, client-ready deliverable.

## Setup

```bash
pip install -r requirements.txt
python src/fetch_data.py
python src/forecast.py
streamlit run src/dashboard.py
```

## Possible extensions

- Add OPEC production data or EIA inventory data as a second data source.
- Swap ARIMA for Prophet or a simple ML model and compare accuracy.
- Add an LLM-generated written summary instead of the rule-based one-liner.
