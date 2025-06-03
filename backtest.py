import argparse
import pandas as pd
from datetime import datetime
import pytz


class Backtester:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.trades = []

    def _compute_heiken_ashi(self):
        df = self.df
        ha_close = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4
        ha_open = ha_close.copy()
        ha_open.iloc[0] = (df['Open'].iloc[0] + df['Close'].iloc[0]) / 2
        for i in range(1, len(df)):
            ha_open.iloc[i] = (ha_open.iloc[i-1] + ha_close.iloc[i-1]) / 2
        ha_high = pd.concat([df['High'], ha_open, ha_close], axis=1).max(axis=1)
        ha_low = pd.concat([df['Low'], ha_open, ha_close], axis=1).min(axis=1)
        self.df['HA_Open'] = ha_open
        self.df['HA_High'] = ha_high
        self.df['HA_Low'] = ha_low
        self.df['HA_Close'] = ha_close

    def _compute_ema(self, length=100):
        self.df['EMA'] = self.df['HA_Close'].ewm(span=length, adjust=False).mean()

    def _is_clean_pullback(self, idx, direction):
        df = self.df
        if idx < 2:
            return False
        candles = df.iloc[idx-2:idx]
        if direction == 'buy':
            # two red candles with no upper wicks
            cond_color = (candles['HA_Close'] < candles['HA_Open']).all()
            cond_wick = (candles['HA_High'] == candles['HA_Open']).all()
            return cond_color and cond_wick
        else:
            cond_color = (candles['HA_Close'] > candles['HA_Open']).all()
            cond_wick = (candles['HA_Low'] == candles['HA_Open']).all()
            return cond_color and cond_wick

    def _is_high_volume_doji(self, idx):
        df = self.df
        if idx < 3:
            return False
        body = abs(df['HA_Close'].iloc[idx] - df['HA_Open'].iloc[idx])
        candle_range = df['HA_High'].iloc[idx] - df['HA_Low'].iloc[idx]
        if candle_range == 0:
            return False
        body_ratio = body / candle_range
        if body_ratio > 0.1:
            return False
        vol = df['Volume'].iloc[idx]
        prev_vol = df['Volume'].iloc[idx-3:idx]
        if vol >= prev_vol.max():
            return True
        return False

    def run(self):
        df = self.df
        self._compute_heiken_ashi()
        self._compute_ema()

        in_position = False
        entry_price = 0
        stop_price = 0
        entry_idx = 0
        direction = None

        for i in range(100, len(df)):
            if not in_position:
                price = df['HA_Close'].iloc[i]
                ema = df['EMA'].iloc[i]
                if price > ema:
                    trend = 'buy'
                elif price < ema:
                    trend = 'sell'
                else:
                    trend = None
                if trend and self._is_clean_pullback(i, trend) and self._is_high_volume_doji(i):
                    in_position = True
                    entry_price = price
                    risk = df['HA_Close'].iloc[i] - df['HA_Low'].iloc[i] if trend == 'buy' else df['HA_High'].iloc[i] - df['HA_Close'].iloc[i]
                    stop_price = entry_price - risk if trend == 'buy' else entry_price + risk
                    tp_price = entry_price + risk if trend == 'buy' else entry_price - risk
                    entry_idx = i
                    direction = trend
                    self.trades.append({'entry_time': df['Timestamp'].iloc[i],
                                        'entry_price': entry_price,
                                        'stop': stop_price,
                                        'tp': tp_price,
                                        'direction': direction,
                                        'exit_time': None,
                                        'result': None})
            else:
                # manage trade
                last_trade = self.trades[-1]
                high = df['HA_High'].iloc[i]
                low = df['HA_Low'].iloc[i]
                if direction == 'buy':
                    if low <= last_trade['stop']:
                        result = -1
                        exit_price = last_trade['stop']
                    elif high >= last_trade['tp']:
                        result = 1
                        exit_price = last_trade['tp']
                    else:
                        continue
                else:
                    if high >= last_trade['stop']:
                        result = -1
                        exit_price = last_trade['stop']
                    elif low <= last_trade['tp']:
                        result = 1
                        exit_price = last_trade['tp']
                    else:
                        continue
                in_position = False
                last_trade['exit_time'] = df['Timestamp'].iloc[i]
                last_trade['exit_price'] = exit_price
                last_trade['result'] = result

    def summary(self):
        if not self.trades:
            return {}
        wins = sum(1 for t in self.trades if t['result'] == 1)
        losses = sum(1 for t in self.trades if t['result'] == -1)
        total = len(self.trades)
        ratio = wins / max(losses, 1)
        df = pd.DataFrame(self.trades)
        df['day'] = df['entry_time'].dt.day_name()
        best_days = df[df['result']==1]['day'].value_counts()
        return {
            'total_trades': total,
            'wins': wins,
            'losses': losses,
            'risk_reward': ratio,
            'best_days': best_days.to_dict()
        }


def load_data(path, from_tz='US/Central', to_tz='Asia/Kolkata'):
    df = pd.read_csv(path)
    if 'Timestamp' not in df.columns:
        raise ValueError('CSV must contain Timestamp column')
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    tz_from = pytz.timezone(from_tz)
    tz_to = pytz.timezone(to_tz)
    df['Timestamp'] = df['Timestamp'].dt.tz_localize(tz_from).dt.tz_convert(tz_to)
    return df


def main():
    parser = argparse.ArgumentParser(description='Backtest Heiken Ashi 100 EMA strategy')
    parser.add_argument('--csv', required=True, help='Path to CSV file')
    parser.add_argument('--from-tz', default='US/Central', help='Timezone of data')
    args = parser.parse_args()

    df = load_data(args.csv, from_tz=args.from_tz)
    bt = Backtester(df)
    bt.run()
    summary = bt.summary()
    if not summary:
        print('No trades found')
    else:
        print('Total trades:', summary['total_trades'])
        print('Wins:', summary['wins'])
        print('Losses:', summary['losses'])
        print('Risk Reward Ratio:', summary['risk_reward'])
        print('Best days:', summary['best_days'])


if __name__ == '__main__':
    main()
