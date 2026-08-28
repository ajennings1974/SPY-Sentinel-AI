import os
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
from dotenv import load_dotenv

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.enums import DataFeed

load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
PAPER_MODE = os.getenv("ALPACA_PAPER_TRADE", "false").lower() == "true"

if not API_KEY or not SECRET_KEY:
    raise RuntimeError("Missing Alpaca API credentials.")

if not PAPER_MODE:
    raise RuntimeError("SAFETY STOP: Paper trading is not enabled.")

print("=" * 55)
print("SPY SENTINEL AI — VERSION 0.1")
print("MODE: PAPER TRADING ONLY")
print("=" * 55)

trading = TradingClient(API_KEY, SECRET_KEY, paper=True)
account = trading.get_account()

print(f"Account status: {account.status}")
print(f"Portfolio value: ${float(account.portfolio_value):,.2f}")
print(f"Buying power:    ${float(account.buying_power):,.2f}")

data = StockHistoricalDataClient(API_KEY, SECRET_KEY)

end = datetime.now(timezone.utc)
start = end - timedelta(days=5)

request = StockBarsRequest(
    symbol_or_symbols=["SPY"],
    timeframe=TimeFrame(5, TimeFrameUnit.Minute),
    start=start,
    end=end,
    feed=DataFeed.IEX,
)

bars = data.get_stock_bars(request).df

if bars.empty:
    raise RuntimeError("No SPY market data returned.")

if isinstance(bars.index, pd.MultiIndex):
    bars = bars.xs("SPY")

bars = bars.sort_index().copy()

bars["ema9"] = bars["close"].ewm(span=9, adjust=False).mean()
bars["ema21"] = bars["close"].ewm(span=21, adjust=False).mean()

delta = bars["close"].diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)
avg_gain = gain.rolling(14).mean()
avg_loss = loss.rolling(14).mean()
rs = avg_gain / avg_loss.replace(0, np.nan)
bars["rsi14"] = 100 - (100 / (1 + rs))

latest = bars.iloc[-1]

price = float(latest["close"])
ema9 = float(latest["ema9"])
ema21 = float(latest["ema21"])
rsi = float(latest["rsi14"])

bull = 0
bear = 0
reasons = []

if price > ema9:
    bull += 1
    reasons.append("Price above EMA9")
else:
    bear += 1
    reasons.append("Price below EMA9")

if ema9 > ema21:
    bull += 1
    reasons.append("EMA9 above EMA21")
else:
    bear += 1
    reasons.append("EMA9 below EMA21")

if 52 <= rsi <= 70:
    bull += 1
    reasons.append("RSI supports bullish momentum")
elif 30 <= rsi <= 48:
    bear += 1
    reasons.append("RSI supports bearish momentum")
else:
    reasons.append("RSI neutral/extreme")

if bull >= 3:
    decision = "BULLISH"
elif bear >= 3:
    decision = "BEARISH"
else:
    decision = "NO TRADE"

print("\nMARKET READ")
print(f"SPY price: ${price:.2f}")
print(f"EMA 9:     ${ema9:.2f}")
print(f"EMA 21:    ${ema21:.2f}")
print(f"RSI 14:    {rsi:.1f}")

print("\nDECISION")
print(f">>> {decision} <<<")
print(f"Bull score: {bull}/3")
print(f"Bear score: {bear}/3")

print("\nWHY")
for reason in reasons:
    print(f"- {reason}")

print("\nRISK GATE")
print("PASS: PAPER TRADING ONLY")
print("NO ORDER WAS PLACED")
print("=" * 55)

from pathlib import Path

log_file = Path("spy_sentinel_signal_log.csv")
log_row = pd.DataFrame([{
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "spy_price": round(price, 2),
    "ema9": round(ema9, 2),
    "ema21": round(ema21, 2),
    "rsi14": round(rsi, 2),
    "bull_score": bull,
    "bear_score": bear,
    "decision": decision,
    "paper_only": True,
}])

if log_file.exists():
    log_row.to_csv(log_file, mode="a", header=False, index=False)
else:
    log_row.to_csv(log_file, index=False)

print(f"\nSignal saved to: {log_file}")
