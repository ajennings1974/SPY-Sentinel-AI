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

print("\nRISK CONTROL CHECK")

risk_reasons = []
risk_pass = True

if rsi >= 75 or rsi <= 25:
    risk_pass = False
    risk_reasons.append("RSI too extreme")

if abs(price - ema21) / ema21 > 0.02:
    risk_pass = False
    risk_reasons.append("Price too far from EMA21")

if decision == "NO TRADE":
    risk_pass = False
    risk_reasons.append("Signal strength insufficient")

if risk_pass:
    final_action = decision
    print("PASS")
    print(f"Eligible direction: {final_action}")
else:
    final_action = "NO TRADE"
    print("BLOCKED")
    for reason in risk_reasons:
        print(f"- {reason}")

print("\nFINAL ACTION")
print(f">>> {final_action} <<<")
print("NO ORDER WAS PLACED")

print("\nOPTIONS CANDIDATE PREVIEW")

if final_action == "BULLISH":
    option_bias = "CALL"
elif final_action == "BEARISH":
    option_bias = "PUT"
else:
    option_bias = "NONE"

print(f"Option bias: {option_bias}")

if option_bias == "NONE":
    print("No options contract will be selected because risk controls blocked the trade.")
else:
    print("Next stage will search for:")
    print("- SPY options only")
    print("- Near-the-money strike")
    print("- Short-dated expiration")
    print("- Paper-trading environment")
    print("- No order submission yet")

print("\nSAFETY STATUS")
print("ORDER SUBMISSION: DISABLED")

import requests
from datetime import date, timedelta

print("\nLIVE OPTIONS CHAIN CHECK")

headers = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY,
}

today = date.today()
exp_start = today + timedelta(days=1)
exp_end = today + timedelta(days=14)

strike_low = round(price * 0.98, 2)
strike_high = round(price * 1.02, 2)

contracts_url = "https://paper-api.alpaca.markets/v2/options/contracts"
contract_params = {
    "underlying_symbols": "SPY",
    "status": "active",
    "expiration_date_gte": exp_start.isoformat(),
    "expiration_date_lte": exp_end.isoformat(),
    "strike_price_gte": strike_low,
    "strike_price_lte": strike_high,
    "limit": 100,
}

response = requests.get(
    contracts_url,
    headers=headers,
    params=contract_params,
    timeout=20
)

response.raise_for_status()

contracts = response.json().get("option_contracts", [])

print(f"Contracts found near SPY price: {len(contracts)}")

if not contracts:
    print("No contracts found in the selected expiration/strike window.")
    candidate = None
else:
    desired_type = None

    if final_action == "BULLISH":
        desired_type = "call"
    elif final_action == "BEARISH":
        desired_type = "put"

    usable = [
        c for c in contracts
        if c.get("tradable") is True
        and (desired_type is None or c.get("type") == desired_type)
    ]

    usable.sort(
        key=lambda c: (
            abs(float(c["strike_price"]) - price),
            c["expiration_date"]
        )
    )

    candidate = usable[0] if usable else None

if candidate:
    symbol = candidate["symbol"]

    print("\nCANDIDATE CONTRACT")
    print(f"Symbol:     {symbol}")
    print(f"Type:       {candidate.get('type')}")
    print(f"Strike:     ${float(candidate.get('strike_price')):.2f}")
    print(f"Expiration: {candidate.get('expiration_date')}")
    print(f"Tradable:   {candidate.get('tradable')}")

    snapshot_url = "https://data.alpaca.markets/v1beta1/options/snapshots"
    snapshot_params = {
        "symbols": symbol,
        "feed": "indicative",
        "limit": 10,
    }

    snap_response = requests.get(
        snapshot_url,
        headers=headers,
        params=snapshot_params,
        timeout=20
    )

    snap_response.raise_for_status()

    snapshots = snap_response.json().get("snapshots", {})
    snap = snapshots.get(symbol, {})

    quote = snap.get("latestQuote") or snap.get("latest_quote") or {}
    greeks = snap.get("greeks") or {}

    bid = quote.get("bp")
    ask = quote.get("ap")

    print("\nCANDIDATE MARKET DATA")
    print(f"Bid:   {bid}")
    print(f"Ask:   {ask}")
    print(f"Delta: {greeks.get('delta')}")
    print(f"Gamma: {greeks.get('gamma')}")
    print(f"Theta: {greeks.get('theta')}")
    print(f"Vega:  {greeks.get('vega')}")

    if bid is not None and ask is not None:
        mid = (float(bid) + float(ask)) / 2
        spread = float(ask) - float(bid)
        print(f"Mid:   {mid:.2f}")
        print(f"Spread:{spread:.2f}")

else:
    print("\nCANDIDATE CONTRACT")
    print("NONE — no eligible contract selected.")

print("\nOPTIONS SAFETY")
print("CHAIN LOOKUP: ENABLED")
print("ORDER SUBMISSION: DISABLED")
print("NO OPTION ORDER WAS PLACED")

print("\nCONTRACT QUALITY CHECK")

quality_pass = True
quality_reasons = []

if candidate:
    strike = float(candidate.get("strike_price"))
    strike_distance_pct = abs(strike - price) / price

    if strike_distance_pct > 0.015:
        quality_pass = False
        quality_reasons.append("Strike is too far from SPY price")

    if bid is None or ask is None:
        quality_pass = False
        quality_reasons.append("Missing bid/ask quote")
    else:
        bid_f = float(bid)
        ask_f = float(ask)

        if bid_f <= 0 or ask_f <= 0:
            quality_pass = False
            quality_reasons.append("Invalid bid/ask")

        spread = ask_f - bid_f
        mid = (ask_f + bid_f) / 2 if (ask_f + bid_f) > 0 else 0

        if mid > 0:
            spread_pct = spread / mid
        else:
            spread_pct = 999

        if spread_pct > 0.20:
            quality_pass = False
            quality_reasons.append("Bid/ask spread too wide")

        estimated_contract_cost = ask_f * 100

        if estimated_contract_cost > 1500:
            quality_pass = False
            quality_reasons.append("Contract cost above $1,500 test cap")

    delta_val = greeks.get("delta")

    if delta_val is None:
        quality_pass = False
        quality_reasons.append("Delta unavailable")
    else:
        delta_abs = abs(float(delta_val))
        if not 0.35 <= delta_abs <= 0.65:
            quality_pass = False
            quality_reasons.append("Delta outside 0.35–0.65 target range")

    print(f"Strike distance: {strike_distance_pct * 100:.2f}%")

    if bid is not None and ask is not None:
        print(f"Estimated contract cost: ${float(ask) * 100:,.2f}")
        if mid > 0:
            print(f"Spread percentage: {spread_pct * 100:.1f}%")

    print(f"Delta absolute value: {abs(float(delta_val)):.3f}" if delta_val is not None else "Delta: unavailable")

else:
    quality_pass = False
    quality_reasons.append("No candidate contract available")

if final_action == "NO TRADE":
    quality_pass = False
    quality_reasons.append("Directional/risk gate already blocked trade")

if quality_pass:
    contract_status = "PASS"
else:
    contract_status = "BLOCKED"

print(f"\nCONTRACT STATUS: {contract_status}")

if quality_reasons:
    for reason in quality_reasons:
        print(f"- {reason}")

if quality_pass and candidate:
    proposed_symbol = candidate["symbol"]
else:
    proposed_symbol = None

print("\nTRADE READINESS")
print(f"Direction: {final_action}")
print(f"Contract: {proposed_symbol if proposed_symbol else 'NONE'}")
print(f"Ready for paper-order simulation: {quality_pass}")
print("ORDER SUBMISSION: DISABLED")
print("NO OPTION ORDER WAS PLACED")

print("\nPOSITION SIZING")

account_value = float(account.portfolio_value)

MAX_RISK_PCT = 0.005
MAX_CONTRACTS = 3

risk_budget = account_value * MAX_RISK_PCT

sim_qty = 0
sim_limit_price = None
sim_symbol = None

if candidate and bid is not None and ask is not None and quality_pass:
    ask_f = float(ask)
    contract_cost = ask_f * 100

    if contract_cost > 0:
        affordable_qty = int(risk_budget // contract_cost)
        sim_qty = max(0, min(affordable_qty, MAX_CONTRACTS))

    sim_symbol = candidate["symbol"]
    sim_limit_price = round((float(bid) + float(ask)) / 2, 2)

print(f"Account value: ${account_value:,.2f}")
print(f"Risk budget (0.5%): ${risk_budget:,.2f}")
print(f"Maximum contracts allowed: {MAX_CONTRACTS}")
print(f"Calculated quantity: {sim_qty}")

print("\nSIMULATED ORDER TICKET")

if (
    final_action != "NO TRADE"
    and quality_pass
    and sim_symbol
    and sim_qty >= 1
):
    ticket_status = "READY"

    print(f"Status:      {ticket_status}")
    print(f"Symbol:      {sim_symbol}")
    print(f"Direction:   {final_action}")
    print(f"Quantity:    {sim_qty}")
    print(f"Order type:  LIMIT")
    print(f"Limit price: ${sim_limit_price:.2f}")
    print("Environment: PAPER")
else:
    ticket_status = "BLOCKED"

    print(f"Status: {ticket_status}")
    print("Reason: One or more safety gates did not pass.")

print("\nEXECUTION LOCK")
print("SUBMIT_ORDER = FALSE")
print("THIS IS A SIMULATION ONLY")
print("NO ORDER WAS SENT TO ALPACA")
