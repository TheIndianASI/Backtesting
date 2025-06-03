# Backtesting

This repository contains a simple backtesting script that implements a Heiken Ashi + 100 EMA strategy.

## Usage

```
python backtest.py --csv path/to/data.csv --from-tz CST
```

The CSV file should include the columns `Timestamp`, `Open`, `High`, `Low`, `Close`, and `Volume`. Timestamps are converted from the provided timezone (default `US/Central`) to Indian Standard Time before analysis.

The script outputs the number of trades, wins, losses, risk/reward ratio, and the most profitable days.
