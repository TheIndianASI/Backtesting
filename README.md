# Backtesting

This repository contains a simple backtesting script that implements a Heiken Ashi + 100 EMA strategy.

## Usage

```
python backtest.py --csv path/to/data.csv --from-tz CST
```

The CSV file should include the columns `Timestamp`, `Open`, `High`, `Low`, `Close`, and `Volume`. Timestamps are converted from the provided timezone (default `US/Central`) to Indian Standard Time before analysis.

The script outputs the number of trades, wins, losses, a win/loss ratio, and the most profitable days.

## Running as a Web Service

A small FastAPI application is included to expose the backtester over HTTP. Run it with:

```
uvicorn server:app --reload
```

Send a POST request to `/backtest` with a CSV file in the form field `file`. The endpoint returns a JSON summary that can be consumed by a front end.
