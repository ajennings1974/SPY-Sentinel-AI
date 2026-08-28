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

from pathlib import Path

print("\nAUDIT LOG")

audit_file = Path("spy_sentinel_audit_log.csv")

audit_row = pd.DataFrame([{
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "spy_price": round(price, 2),
    "ema9": round(ema9, 2),
    "ema21": round(ema21, 2),
    "rsi14": round(rsi, 2),
    "bull_score": bull,
    "bear_score": bear,
    "signal_decision": decision,
    "risk_pass": risk_pass,
    "final_action": final_action,
    "option_bias": option_bias,
    "candidate_symbol": candidate["symbol"] if candidate else "",
    "contract_quality_pass": quality_pass,
    "contract_status": contract_status,
    "simulated_qty": sim_qty,
    "simulated_limit_price": sim_limit_price if sim_limit_price is not None else "",
    "ticket_status": ticket_status,
    "paper_mode": PAPER_MODE,
    "order_submission_enabled": False,
}])

if audit_file.exists():
    audit_row.to_csv(audit_file, mode="a", header=False, index=False)
else:
    audit_row.to_csv(audit_file, index=False)

print(f"Audit record saved to: {audit_file}")
print("AUDIT COMPLETE")

print("\n" + "=" * 55)
print("SPY SENTINEL AI — RUN SUMMARY")
print("=" * 55)

print(f"SPY Price:        ${price:.2f}")
print(f"Signal:           {decision}")
print(f"Final Action:     {final_action}")
print(f"Risk Gate:        {'PASS' if risk_pass else 'BLOCKED'}")
print(f"Contract Status:  {contract_status}")
print(f"Option Bias:      {option_bias}")
print(f"Candidate:        {candidate['symbol'] if candidate else 'NONE'}")
print(f"Simulated Qty:    {sim_qty}")
print(f"Ticket Status:    {ticket_status}")
print(f"Paper Mode:       {PAPER_MODE}")
print("Order Submitted:  NO")

if risk_reasons:
    print("\nRisk Notes:")
    for item in risk_reasons:
        print(f"- {item}")

if quality_reasons:
    print("\nContract Notes:")
    for item in quality_reasons:
        print(f"- {item}")

print("\nAudit File:")
print("spy_sentinel_audit_log.csv")

print("=" * 55)

from zoneinfo import ZoneInfo

print("\nENHANCED SIGNAL CHECK")

bars["typical_price"] = (bars["high"] + bars["low"] + bars["close"]) / 3
bars["vwap"] = (
    (bars["typical_price"] * bars["volume"]).cumsum()
    / bars["volume"].cumsum()
)

bars["avg_volume20"] = bars["volume"].rolling(20).mean()

latest = bars.iloc[-1]

vwap = float(latest["vwap"])
current_volume = float(latest["volume"])
avg_volume20 = float(latest["avg_volume20"])

volume_ratio = current_volume / avg_volume20 if avg_volume20 > 0 else 0

latest_time = pd.Timestamp(bars.index[-1])

if latest_time.tzinfo is None:
    latest_time = latest_time.tz_localize("UTC")

ny_time = latest_time.tz_convert(ZoneInfo("America/New_York"))

minutes_after_open = (
    (ny_time.hour * 60 + ny_time.minute) - (9 * 60 + 30)
)

time_filter_pass = 15 <= minutes_after_open <= 360

enhanced_score = 0
enhanced_notes = []

if decision == "BULLISH" and price > vwap:
    enhanced_score += 1
    enhanced_notes.append("Bullish signal confirmed above VWAP")
elif decision == "BEARISH" and price < vwap:
    enhanced_score += 1
    enhanced_notes.append("Bearish signal confirmed below VWAP")
else:
    enhanced_notes.append("VWAP does not confirm direction")

if volume_ratio >= 1.0:
    enhanced_score += 1
    enhanced_notes.append("Volume at or above 20-bar average")
else:
    enhanced_notes.append("Volume below 20-bar average")

if abs(ema9 - ema21) / price >= 0.0005:
    enhanced_score += 1
    enhanced_notes.append("EMA separation confirms trend")
else:
    enhanced_notes.append("EMA separation too weak")

if time_filter_pass:
    enhanced_score += 1
    enhanced_notes.append("Time-of-day filter passed")
else:
    enhanced_notes.append("Time-of-day filter blocked")

if risk_pass and quality_pass:
    enhanced_score += 1
    enhanced_notes.append("Earlier risk and contract gates passed")
else:
    enhanced_notes.append("Earlier safety gate blocked trade")

enhanced_ready = (
    enhanced_score >= 4
    and final_action != "NO TRADE"
    and quality_pass
)

print(f"VWAP:             ${vwap:.2f}")
print(f"Volume ratio:     {volume_ratio:.2f}x")
print(f"Market time ET:   {ny_time.strftime('%H:%M')}")
print(f"Enhanced score:   {enhanced_score}/5")

for note in enhanced_notes:
    print(f"- {note}")

print("\nV1.0 DECISION")
print(f"Enhanced READY: {enhanced_ready}")
print("ORDER SUBMISSION: DISABLED")

enhanced_audit_file = Path("spy_sentinel_v10_audit.csv")

enhanced_row = pd.DataFrame([{
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "spy_price": round(price, 2),
    "vwap": round(vwap, 2),
    "volume_ratio": round(volume_ratio, 2),
    "enhanced_score": enhanced_score,
    "enhanced_ready": enhanced_ready,
    "final_action": final_action,
    "contract_status": contract_status,
    "paper_only": True,
    "order_submitted": False,
}])

if enhanced_audit_file.exists():
    enhanced_row.to_csv(
        enhanced_audit_file,
        mode="a",
        header=False,
        index=False
    )
else:
    enhanced_row.to_csv(enhanced_audit_file, index=False)

print(f"V1.0 audit saved to: {enhanced_audit_file}")

print("\nV1.1 MARKET REGIME CHECK")

# ATR
high_low = bars["high"] - bars["low"]
high_close = (bars["high"] - bars["close"].shift()).abs()
low_close = (bars["low"] - bars["close"].shift()).abs()

true_range = pd.concat(
    [high_low, high_close, low_close],
    axis=1
).max(axis=1)

bars["atr14"] = true_range.rolling(14).mean()

atr14 = float(bars["atr14"].iloc[-1])
atr_pct = atr14 / price if price > 0 else 0

# EMA slopes over recent bars
ema9_slope = float(bars["ema9"].iloc[-1] - bars["ema9"].iloc[-4])
ema21_slope = float(bars["ema21"].iloc[-1] - bars["ema21"].iloc[-4])

# Data freshness
now_utc = pd.Timestamp.now(tz="UTC")
bar_time_utc = pd.Timestamp(bars.index[-1])

if bar_time_utc.tzinfo is None:
    bar_time_utc = bar_time_utc.tz_localize("UTC")

bar_age_minutes = (now_utc - bar_time_utc).total_seconds() / 60

fresh_data = bar_age_minutes <= 20

# Regime classification
if ema9 > ema21 and ema9_slope > 0 and ema21_slope > 0:
    regime = "UPTREND"
elif ema9 < ema21 and ema9_slope < 0 and ema21_slope < 0:
    regime = "DOWNTREND"
else:
    regime = "CHOPPY"

regime_score = 0
regime_notes = []

if final_action == "BULLISH" and regime == "UPTREND":
    regime_score += 1
    regime_notes.append("Bullish action matches uptrend")
elif final_action == "BEARISH" and regime == "DOWNTREND":
    regime_score += 1
    regime_notes.append("Bearish action matches downtrend")
else:
    regime_notes.append("Direction does not match market regime")

if 0.001 <= atr_pct <= 0.015:
    regime_score += 1
    regime_notes.append("ATR volatility is inside acceptable range")
else:
    regime_notes.append("ATR volatility outside target range")

if fresh_data:
    regime_score += 1
    regime_notes.append("Market data is fresh")
else:
    regime_notes.append("Market data is stale")

v11_ready = (
    enhanced_ready
    and regime_score >= 3
    and fresh_data
)

print(f"Regime:           {regime}")
print(f"ATR 14:           ${atr14:.2f}")
print(f"ATR %:            {atr_pct * 100:.2f}%")
print(f"EMA9 slope:       {ema9_slope:.4f}")
print(f"EMA21 slope:      {ema21_slope:.4f}")
print(f"Bar age:          {bar_age_minutes:.1f} minutes")
print(f"Regime score:     {regime_score}/3")

for note in regime_notes:
    print(f"- {note}")

print("\nV1.1 READINESS")
print(f"Ready: {v11_ready}")
print("ORDER SUBMISSION: DISABLED")
print("NO ORDER WAS PLACED")

v11_audit = Path("spy_sentinel_v11_audit.csv")

v11_row = pd.DataFrame([{
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "spy_price": round(price, 2),
    "regime": regime,
    "atr14": round(atr14, 4),
    "atr_pct": round(atr_pct, 6),
    "ema9_slope": round(ema9_slope, 6),
    "ema21_slope": round(ema21_slope, 6),
    "bar_age_minutes": round(bar_age_minutes, 2),
    "fresh_data": fresh_data,
    "enhanced_ready": enhanced_ready,
    "regime_score": regime_score,
    "v11_ready": v11_ready,
    "final_action": final_action,
    "paper_only": True,
    "order_submitted": False,
}])

if v11_audit.exists():
    v11_row.to_csv(v11_audit, mode="a", header=False, index=False)
else:
    v11_row.to_csv(v11_audit, index=False)

print(f"V1.1 audit saved to: {v11_audit}")

print("\nV1.2 MULTI-TIMEFRAME CHECK")

bars15 = bars.resample("15min").agg({
    "open": "first",
    "high": "max",
    "low": "min",
    "close": "last",
    "volume": "sum"
}).dropna()

bars15["ema9"] = bars15["close"].ewm(span=9, adjust=False).mean()
bars15["ema21"] = bars15["close"].ewm(span=21, adjust=False).mean()

last15 = bars15.iloc[-1]

price15 = float(last15["close"])
ema9_15 = float(last15["ema9"])
ema21_15 = float(last15["ema21"])

if ema9_15 > ema21_15:
    trend15 = "BULLISH"
elif ema9_15 < ema21_15:
    trend15 = "BEARISH"
else:
    trend15 = "NEUTRAL"

if final_action == "BULLISH":
    timeframe_match = trend15 == "BULLISH"
elif final_action == "BEARISH":
    timeframe_match = trend15 == "BEARISH"
else:
    timeframe_match = False

print(f"15m price:       ${price15:.2f}")
print(f"15m EMA9:        ${ema9_15:.2f}")
print(f"15m EMA21:       ${ema21_15:.2f}")
print(f"15m trend:       {trend15}")
print(f"Timeframe match: {timeframe_match}")

print("\nCONFIDENCE ENGINE")

confidence = 0
confidence_notes = []

if enhanced_score >= 4:
    confidence += 25
    confidence_notes.append("+25 enhanced signal")
else:
    confidence_notes.append("+0 enhanced signal")

if regime_score == 3:
    confidence += 25
    confidence_notes.append("+25 market regime")
else:
    confidence_notes.append("+0 market regime")

if timeframe_match:
    confidence += 25
    confidence_notes.append("+25 15-minute confirmation")
else:
    confidence_notes.append("+0 15-minute confirmation")

if quality_pass:
    confidence += 25
    confidence_notes.append("+25 contract quality")
else:
    confidence_notes.append("+0 contract quality")

V12_MIN_CONFIDENCE = 75

v12_ready = (
    confidence >= V12_MIN_CONFIDENCE
    and v11_ready
    and timeframe_match
)

print(f"Confidence:      {confidence}/100")
print(f"Required:        {V12_MIN_CONFIDENCE}/100")

for note in confidence_notes:
    print(f"- {note}")

print("\nV1.2 FINAL READINESS")
print(f"Ready: {v12_ready}")
print("ORDER SUBMISSION: DISABLED")
print("NO ORDER WAS PLACED")

v12_audit_file = Path("spy_sentinel_v12_audit.csv")

v12_row = pd.DataFrame([{
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "spy_price": round(price, 2),
    "five_minute_regime": regime,
    "fifteen_minute_trend": trend15,
    "timeframe_match": timeframe_match,
    "enhanced_score": enhanced_score,
    "regime_score": regime_score,
    "contract_quality_pass": quality_pass,
    "confidence": confidence,
    "minimum_confidence": V12_MIN_CONFIDENCE,
    "v12_ready": v12_ready,
    "final_action": final_action,
    "paper_only": True,
    "order_submitted": False,
}])

if v12_audit_file.exists():
    v12_row.to_csv(v12_audit_file, mode="a", header=False, index=False)
else:
    v12_row.to_csv(v12_audit_file, index=False)

print(f"V1.2 audit saved to: {v12_audit_file}")

print("\nV1.3 EXECUTION SAFETY CHECK")

MAX_TRADES_PER_DAY = 3
COOLDOWN_MINUTES = 30
PAPER_EXECUTION_ALLOWED = False

today_et = datetime.now(ZoneInfo("America/New_York")).date()

history_file = Path("spy_sentinel_execution_history.csv")

trades_today = 0
minutes_since_last_ready = None

if history_file.exists():
    history = pd.read_csv(history_file)

    if not history.empty:
        history["timestamp_utc"] = pd.to_datetime(
            history["timestamp_utc"],
            utc=True,
            errors="coerce"
        )

        history["date_et"] = (
            history["timestamp_utc"]
            .dt.tz_convert("America/New_York")
            .dt.date
        )

        trades_today = int(
            (
                (history["date_et"] == today_et)
                & (history["ticket_status"] == "READY")
            ).sum()
        )

        ready_rows = history[history["ticket_status"] == "READY"]

        if not ready_rows.empty:
            last_ready = ready_rows["timestamp_utc"].max()
            now_ts = pd.Timestamp.now(tz="UTC")
            minutes_since_last_ready = (
                now_ts - last_ready
            ).total_seconds() / 60

daily_limit_pass = trades_today < MAX_TRADES_PER_DAY

cooldown_pass = (
    minutes_since_last_ready is None
    or minutes_since_last_ready >= COOLDOWN_MINUTES
)

print(f"Ready tickets today: {trades_today}/{MAX_TRADES_PER_DAY}")
print(f"Daily limit pass:     {daily_limit_pass}")
print(f"Cooldown pass:        {cooldown_pass}")

if minutes_since_last_ready is not None:
    print(f"Minutes since last READY: {minutes_since_last_ready:.1f}")
else:
    print("Minutes since last READY: NONE")

v13_ready = (
    v12_ready
    and daily_limit_pass
    and cooldown_pass
    and PAPER_MODE
)

print("\nV1.3 MASTER GATE")
print(f"Signal/strategy ready: {v12_ready}")
print(f"Daily limit ready:     {daily_limit_pass}")
print(f"Cooldown ready:        {cooldown_pass}")
print(f"Paper mode confirmed:  {PAPER_MODE}")
print(f"MASTER READY:          {v13_ready}")

if v13_ready and PAPER_EXECUTION_ALLOWED:
    execution_status = "READY_TO_SUBMIT_PAPER"
elif v13_ready:
    execution_status = "DRY_RUN_READY"
else:
    execution_status = "BLOCKED"

print(f"Execution status:      {execution_status}")

print("\nHARD LOCK")
print(f"PAPER_EXECUTION_ALLOWED = {PAPER_EXECUTION_ALLOWED}")
print("LIVE TRADING ALLOWED = FALSE")
print("NO ORDER WAS SUBMITTED")

execution_row = pd.DataFrame([{
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "spy_price": round(price, 2),
    "final_action": final_action,
    "confidence": confidence,
    "v12_ready": v12_ready,
    "daily_limit_pass": daily_limit_pass,
    "cooldown_pass": cooldown_pass,
    "master_ready": v13_ready,
    "ticket_status": "READY" if v13_ready else "BLOCKED",
    "execution_status": execution_status,
    "paper_execution_allowed": PAPER_EXECUTION_ALLOWED,
    "order_submitted": False,
}])

if history_file.exists():
    execution_row.to_csv(
        history_file,
        mode="a",
        header=False,
        index=False
    )
else:
    execution_row.to_csv(history_file, index=False)

print(f"Execution history saved to: {history_file}")

print("\nV1.4 SESSION SAFETY")

market_open = ny_time.hour > 9 or (ny_time.hour == 9 and ny_time.minute >= 30)
market_before_close = ny_time.hour < 15 or (ny_time.hour == 15 and ny_time.minute <= 45)

regular_session = market_open and market_before_close

avoid_first_15 = minutes_after_open >= 15
avoid_last_15 = minutes_after_open <= 375

session_pass = regular_session and avoid_first_15 and avoid_last_15

print(f"Regular session:   {regular_session}")
print(f"After first 15m:   {avoid_first_15}")
print(f"Before final 15m:  {avoid_last_15}")
print(f"Session pass:      {session_pass}")

print("\nLOSS-CONTROL GUARD")

MAX_DAILY_LOSS_PCT = 0.02
MAX_CONSECUTIVE_LOSSES = 3

daily_loss_lock = False
consecutive_loss_lock = False

loss_log = Path("spy_sentinel_trade_results.csv")

daily_pnl = 0.0
consecutive_losses = 0

if loss_log.exists():
    results = pd.read_csv(loss_log)

    if not results.empty and "pnl" in results.columns:
        results["timestamp_utc"] = pd.to_datetime(
            results["timestamp_utc"],
            utc=True,
            errors="coerce"
        )

        results["date_et"] = (
            results["timestamp_utc"]
            .dt.tz_convert("America/New_York")
            .dt.date
        )

        today_results = results[results["date_et"] == today_et]
        daily_pnl = float(today_results["pnl"].sum())

        recent = results.sort_values("timestamp_utc").tail(10)

        for pnl in reversed(recent["pnl"].tolist()):
            if pnl < 0:
                consecutive_losses += 1
            else:
                break

daily_loss_limit = -(account_value * MAX_DAILY_LOSS_PCT)

if daily_pnl <= daily_loss_limit:
    daily_loss_lock = True

if consecutive_losses >= MAX_CONSECUTIVE_LOSSES:
    consecutive_loss_lock = True

loss_guard_pass = not daily_loss_lock and not consecutive_loss_lock

print(f"Daily P&L:             ${daily_pnl:,.2f}")
print(f"Daily loss limit:      ${daily_loss_limit:,.2f}")
print(f"Consecutive losses:    {consecutive_losses}")
print(f"Loss guard pass:       {loss_guard_pass}")

v14_ready = (
    v13_ready
    and session_pass
    and loss_guard_pass
)

print("\nV1.4 FINAL SAFETY GATE")
print(f"V1.3 ready:        {v13_ready}")
print(f"Session pass:      {session_pass}")
print(f"Loss guard pass:   {loss_guard_pass}")
print(f"V1.4 READY:        {v14_ready}")

if v14_ready:
    v14_status = "DRY_RUN_READY"
else:
    v14_status = "BLOCKED"

print(f"Status:            {v14_status}")
print("PAPER EXECUTION:   DISABLED")
print("LIVE EXECUTION:    DISABLED")
print("NO ORDER WAS SENT")

print("\nV1.5 SIGNAL PERSISTENCE CHECK")

recent3 = bars.tail(3).copy()

bullish_bars = (
    (recent3["close"] > recent3["ema9"])
    & (recent3["ema9"] > recent3["ema21"])
)

bearish_bars = (
    (recent3["close"] < recent3["ema9"])
    & (recent3["ema9"] < recent3["ema21"])
)

bullish_persistence = int(bullish_bars.sum())
bearish_persistence = int(bearish_bars.sum())

if final_action == "BULLISH":
    persistence_pass = bullish_persistence >= 2
elif final_action == "BEARISH":
    persistence_pass = bearish_persistence >= 2
else:
    persistence_pass = False

print(f"Bullish bars:      {bullish_persistence}/3")
print(f"Bearish bars:      {bearish_persistence}/3")
print(f"Persistence pass:  {persistence_pass}")

print("\n1-HOUR TREND CHECK")

bars60 = bars.resample("60min").agg({
    "open": "first",
    "high": "max",
    "low": "min",
    "close": "last",
    "volume": "sum"
}).dropna()

bars60["ema9"] = bars60["close"].ewm(span=9, adjust=False).mean()
bars60["ema21"] = bars60["close"].ewm(span=21, adjust=False).mean()

last60 = bars60.iloc[-1]

ema9_60 = float(last60["ema9"])
ema21_60 = float(last60["ema21"])

if ema9_60 > ema21_60:
    trend60 = "BULLISH"
elif ema9_60 < ema21_60:
    trend60 = "BEARISH"
else:
    trend60 = "NEUTRAL"

if final_action == "BULLISH":
    hour_match = trend60 == "BULLISH"
elif final_action == "BEARISH":
    hour_match = trend60 == "BEARISH"
else:
    hour_match = False

print(f"1h EMA9:       ${ema9_60:.2f}")
print(f"1h EMA21:      ${ema21_60:.2f}")
print(f"1h trend:      {trend60}")
print(f"1h match:      {hour_match}")

print("\nOPENING GAP CHECK")

ny_dates = bars.index.tz_convert("America/New_York").date
today_bar_date = ny_time.date()

today_bars = bars[ny_dates == today_bar_date]

gap_pass = True
gap_pct = 0.0

if not today_bars.empty:
    session_open = float(today_bars.iloc[0]["open"])

    prior_bars = bars[ny_dates < today_bar_date]

    if not prior_bars.empty:
        prior_close = float(prior_bars.iloc[-1]["close"])
        gap_pct = (session_open - prior_close) / prior_close

        if abs(gap_pct) > 0.015:
            gap_pass = False

print(f"Opening gap:    {gap_pct * 100:.2f}%")
print(f"Gap limit:      1.50%")
print(f"Gap pass:       {gap_pass}")

v15_ready = (
    v14_ready
    and persistence_pass
    and hour_match
    and gap_pass
)

print("\nV1.5 MASTER READINESS")
print(f"V1.4 ready:          {v14_ready}")
print(f"Persistence pass:    {persistence_pass}")
print(f"1-hour match:        {hour_match}")
print(f"Opening gap pass:    {gap_pass}")
print(f"V1.5 READY:          {v15_ready}")

print("PAPER EXECUTION:     DISABLED")
print("LIVE EXECUTION:      DISABLED")
print("NO ORDER WAS SENT")

print("\nV1.6 EXIT PLAN")

STOP_LOSS_PCT = 0.25
TAKE_PROFIT_PCT = 0.40
MAX_HOLD_MINUTES = 90

planned_entry = None
planned_stop = None
planned_target = None

if candidate and bid is not None and ask is not None:
    planned_entry = round((float(bid) + float(ask)) / 2, 2)
    planned_stop = round(planned_entry * (1 - STOP_LOSS_PCT), 2)
    planned_target = round(planned_entry * (1 + TAKE_PROFIT_PCT), 2)

print(f"Planned entry:       {planned_entry if planned_entry is not None else 'NONE'}")
print(f"Planned stop loss:   {planned_stop if planned_stop is not None else 'NONE'}")
print(f"Planned take profit: {planned_target if planned_target is not None else 'NONE'}")
print(f"Max hold time:       {MAX_HOLD_MINUTES} minutes")

print("\nSHADOW TRADE SIMULATION")

shadow_ready = (
    v15_ready
    and candidate is not None
    and planned_entry is not None
    and sim_qty >= 1
)

if shadow_ready:
    shadow_status = "READY"
else:
    shadow_status = "BLOCKED"

print(f"Shadow status: {shadow_status}")
print(f"Symbol:        {candidate['symbol'] if candidate else 'NONE'}")
print(f"Quantity:      {sim_qty}")
print(f"Direction:     {final_action}")
print("REAL ORDER:    DISABLED")
print("PAPER ORDER:   DISABLED")

shadow_log = Path("spy_sentinel_shadow_trades.csv")

shadow_row = pd.DataFrame([{
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "symbol": candidate["symbol"] if candidate else "",
    "direction": final_action,
    "qty": sim_qty,
    "entry_price": planned_entry if planned_entry is not None else "",
    "stop_price": planned_stop if planned_stop is not None else "",
    "target_price": planned_target if planned_target is not None else "",
    "max_hold_minutes": MAX_HOLD_MINUTES,
    "shadow_ready": shadow_ready,
    "status": shadow_status,
    "paper_order_sent": False,
    "live_order_sent": False,
}])

if shadow_log.exists():
    shadow_row.to_csv(shadow_log, mode="a", header=False, index=False)
else:
    shadow_row.to_csv(shadow_log, index=False)

print(f"Shadow log saved to: {shadow_log}")

print("\nV1.7 QUALITY SCORE")

quality_score = 0

if persistence_pass:
    quality_score += 20

if timeframe_match:
    quality_score += 20

if hour_match:
    quality_score += 20

if gap_pass:
    quality_score += 10

if session_pass:
    quality_score += 10

if loss_guard_pass:
    quality_score += 10

if quality_pass:
    quality_score += 10

print(f"Quality score: {quality_score}/100")

print("\nV1.7 FINAL CLASSIFICATION")

if quality_score >= 80 and shadow_ready:
    trade_grade = "A"
elif quality_score >= 65:
    trade_grade = "B"
elif quality_score >= 50:
    trade_grade = "C"
else:
    trade_grade = "REJECT"

print(f"Trade grade: {trade_grade}")

v17_ready = (
    trade_grade == "A"
    and shadow_ready
)

print(f"V1.7 READY: {v17_ready}")

print("\nFINAL BOT STATUS")

print(f"Signal:            {decision}")
print(f"Final action:      {final_action}")
print(f"Confidence:        {confidence}/100")
print(f"Market regime:     {regime}")
print(f"15m trend:         {trend15}")
print(f"1h trend:          {trend60}")
print(f"Trade grade:       {trade_grade}")
print(f"Shadow ready:      {shadow_ready}")
print(f"V1.7 ready:        {v17_ready}")
print("Paper execution:   DISABLED")
print("Live execution:    DISABLED")
print("NO ORDER WAS SENT")

v17_audit = Path("spy_sentinel_v17_audit.csv")

v17_row = pd.DataFrame([{
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "spy_price": round(price, 2),
    "signal": decision,
    "final_action": final_action,
    "confidence": confidence,
    "regime": regime,
    "trend15": trend15,
    "trend60": trend60,
    "quality_score": quality_score,
    "trade_grade": trade_grade,
    "shadow_ready": shadow_ready,
    "v17_ready": v17_ready,
    "paper_execution": False,
    "live_execution": False,
}])

if v17_audit.exists():
    v17_row.to_csv(v17_audit, mode="a", header=False, index=False)
else:
    v17_row.to_csv(v17_audit, index=False)

print(f"V1.7 audit saved to: {v17_audit}")

print("\nV1.8 BLOCKER DIAGNOSTICS")

blockers = []

if decision == "NO TRADE":
    blockers.append("Base signal did not qualify")

if not risk_pass:
    blockers.append("Risk gate failed")

if not quality_pass:
    blockers.append("Contract quality failed")

if not timeframe_match:
    blockers.append("15-minute trend mismatch")

if not hour_match:
    blockers.append("1-hour trend mismatch")

if not persistence_pass:
    blockers.append("Signal persistence failed")

if not regime_score == 3:
    blockers.append("Market regime confirmation failed")

if not session_pass:
    blockers.append("Session timing failed")

if not loss_guard_pass:
    blockers.append("Loss-control guard failed")

print(f"Total blockers: {len(blockers)}")

for blocker in blockers:
    print(f"- {blocker}")

import json

status_snapshot = {
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "spy_price": round(price, 2),
    "signal": decision,
    "final_action": final_action,
    "confidence": confidence,
    "market_regime": regime,
    "trend_15m": trend15,
    "trend_1h": trend60,
    "trade_grade": trade_grade,
    "shadow_ready": shadow_ready,
    "v17_ready": v17_ready,
    "blocker_count": len(blockers),
    "blockers": blockers,
    "paper_execution_enabled": False,
    "live_execution_enabled": False
}

with open("spy_sentinel_latest_status.json", "w") as f:
    json.dump(status_snapshot, f, indent=2)

print("Latest status saved to: spy_sentinel_latest_status.json")

print("\nPAPER-EXECUTION ELIGIBILITY")

paper_eligible = (
    v17_ready
    and shadow_ready
    and trade_grade == "A"
    and confidence >= 75
    and len(blockers) == 0
)

print(f"Paper eligible: {paper_eligible}")

if paper_eligible:
    print("STATUS: QUALIFIED FOR FUTURE PAPER EXECUTION")
else:
    print("STATUS: NOT QUALIFIED")

print("PAPER ORDER SWITCH: OFF")
print("LIVE ORDER SWITCH: OFF")
print("NO ORDER WAS SENT")

print("\nV1.9 RUN SCOREBOARD")

scoreboard_file = Path("spy_sentinel_scoreboard.csv")

scoreboard_row = pd.DataFrame([{
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "signal": decision,
    "final_action": final_action,
    "confidence": confidence,
    "trade_grade": trade_grade,
    "blocker_count": len(blockers),
    "paper_eligible": paper_eligible,
    "order_sent": False,
}])

if scoreboard_file.exists():
    scoreboard_row.to_csv(
        scoreboard_file,
        mode="a",
        header=False,
        index=False
    )
else:
    scoreboard_row.to_csv(scoreboard_file, index=False)

print(f"Scoreboard updated: {scoreboard_file}")

if scoreboard_file.exists():
    score = pd.read_csv(scoreboard_file)

    total_runs = len(score)
    no_trade_runs = int((score["final_action"] == "NO TRADE").sum())
    bullish_runs = int((score["final_action"] == "BULLISH").sum())
    bearish_runs = int((score["final_action"] == "BEARISH").sum())
    eligible_runs = int(score["paper_eligible"].astype(bool).sum())

    print("\nSCOREBOARD SUMMARY")
    print(f"Total runs:       {total_runs}")
    print(f"No-trade runs:    {no_trade_runs}")
    print(f"Bullish runs:     {bullish_runs}")
    print(f"Bearish runs:     {bearish_runs}")
    print(f"Paper eligible:   {eligible_runs}")

blocker_file = Path("spy_sentinel_blockers.csv")

blocker_rows = []

for blocker in blockers:
    blocker_rows.append({
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "blocker": blocker
    })

if blocker_rows:
    blocker_df = pd.DataFrame(blocker_rows)

    if blocker_file.exists():
        blocker_df.to_csv(
            blocker_file,
            mode="a",
            header=False,
            index=False
        )
    else:
        blocker_df.to_csv(blocker_file, index=False)

print(f"Blocker history updated: {blocker_file}")
print("ORDER SYSTEM REMAINS LOCKED")

print("\nV2.0 BLOCKER FREQUENCY")

if blocker_file.exists():
    blocker_history = pd.read_csv(blocker_file)

    if not blocker_history.empty:
        blocker_counts = (
            blocker_history["blocker"]
            .value_counts()
        )

        print("Most common blockers:")

        for blocker_name, blocker_count in blocker_counts.head(10).items():
            print(f"- {blocker_name}: {blocker_count}")
else:
    print("No blocker history available yet.")

print("\nCONFIDENCE BAND")

if confidence >= 90:
    confidence_band = "VERY HIGH"
elif confidence >= 75:
    confidence_band = "TRADE CANDIDATE"
elif confidence >= 50:
    confidence_band = "WATCH"
elif confidence >= 25:
    confidence_band = "WEAK"
else:
    confidence_band = "NO EDGE"

print(f"Confidence score: {confidence}/100")
print(f"Confidence band:  {confidence_band}")
print("Minimum trade candidate threshold: 75/100")

print("\nV2.0 READINESS REPORT")

readiness_checks = {
    "Base signal": decision != "NO TRADE",
    "Risk gate": risk_pass,
    "Contract quality": quality_pass,
    "15m confirmation": timeframe_match,
    "1h confirmation": hour_match,
    "Persistence": persistence_pass,
    "Regime": regime_score == 3,
    "Session timing": session_pass,
    "Loss guard": loss_guard_pass,
    "Confidence >= 75": confidence >= 75,
}

passed_checks = sum(readiness_checks.values())
total_checks = len(readiness_checks)

for name, passed in readiness_checks.items():
    print(f"{name}: {'PASS' if passed else 'FAIL'}")

print(f"\nReadiness checks passed: {passed_checks}/{total_checks}")
print(f"Readiness percentage: {(passed_checks / total_checks) * 100:.0f}%")
print("ORDER SYSTEM: LOCKED")

print("\nV2.1 MINI HISTORICAL SIGNAL TEST")

test = bars.copy()

test["future_close_30m"] = test["close"].shift(-6)
test["future_return_30m"] = (
    test["future_close_30m"] / test["close"] - 1
)

historical_signals = []

for idx, row in test.iterrows():
    if pd.isna(row.get("rsi14")):
        continue

    row_bull = 0
    row_bear = 0

    if row["close"] > row["ema9"]:
        row_bull += 1
    else:
        row_bear += 1

    if row["ema9"] > row["ema21"]:
        row_bull += 1
    else:
        row_bear += 1

    if 52 <= row["rsi14"] <= 70:
        row_bull += 1
    elif 30 <= row["rsi14"] <= 48:
        row_bear += 1

    if row_bull >= 3:
        hist_signal = "BULLISH"
    elif row_bear >= 3:
        hist_signal = "BEARISH"
    else:
        hist_signal = "NO TRADE"

    historical_signals.append({
        "timestamp": idx,
        "signal": hist_signal,
        "future_return_30m": row["future_return_30m"],
    })

hist_df = pd.DataFrame(historical_signals)

hist_df = hist_df.dropna(subset=["future_return_30m"])

print(f"Historical bars evaluated: {len(hist_df)}")

trade_signals = hist_df[
    hist_df["signal"].isin(["BULLISH", "BEARISH"])
].copy()

if not trade_signals.empty:
    trade_signals["correct"] = (
        ((trade_signals["signal"] == "BULLISH") &
         (trade_signals["future_return_30m"] > 0))
        |
        ((trade_signals["signal"] == "BEARISH") &
         (trade_signals["future_return_30m"] < 0))
    )

    historical_accuracy = trade_signals["correct"].mean() * 100

    bullish_count = int(
        (trade_signals["signal"] == "BULLISH").sum()
    )

    bearish_count = int(
        (trade_signals["signal"] == "BEARISH").sum()
    )

    print(f"Trade signals found: {len(trade_signals)}")
    print(f"Bullish signals:     {bullish_count}")
    print(f"Bearish signals:     {bearish_count}")
    print(f"30-minute accuracy:  {historical_accuracy:.1f}%")
else:
    historical_accuracy = 0.0
    print("No historical trade signals found.")

print("TEST TYPE: RESEARCH ONLY")
print("NO HISTORICAL RESULTS WERE USED TO PLACE AN ORDER")

print("\nV2.2 60-MINUTE HISTORICAL TEST")

test60 = bars.copy()

test60["future_close_60m"] = test60["close"].shift(-12)
test60["future_return_60m"] = (
    test60["future_close_60m"] / test60["close"] - 1
)

hist60 = []

for idx, row in test60.iterrows():
    if pd.isna(row.get("rsi14")):
        continue

    b = 0
    s = 0

    if row["close"] > row["ema9"]:
        b += 1
    else:
        s += 1

    if row["ema9"] > row["ema21"]:
        b += 1
    else:
        s += 1

    if 52 <= row["rsi14"] <= 70:
        b += 1
    elif 30 <= row["rsi14"] <= 48:
        s += 1

    if b >= 3:
        sig = "BULLISH"
    elif s >= 3:
        sig = "BEARISH"
    else:
        sig = "NO TRADE"

    hist60.append({
        "timestamp": idx,
        "signal": sig,
        "future_return_60m": row["future_return_60m"]
    })

hist60_df = pd.DataFrame(hist60).dropna(
    subset=["future_return_60m"]
)

trade60 = hist60_df[
    hist60_df["signal"].isin(["BULLISH", "BEARISH"])
].copy()

if not trade60.empty:
    trade60["correct"] = (
        (
            (trade60["signal"] == "BULLISH")
            & (trade60["future_return_60m"] > 0)
        )
        |
        (
            (trade60["signal"] == "BEARISH")
            & (trade60["future_return_60m"] < 0)
        )
    )

    accuracy60 = trade60["correct"].mean() * 100

    print(f"60m trade signals: {len(trade60)}")
    print(f"60m accuracy:      {accuracy60:.1f}%")
else:
    accuracy60 = 0.0
    print("No 60-minute signals available.")

print("\nDIRECTION BREAKDOWN")

bull_hist = trade_signals[
    trade_signals["signal"] == "BULLISH"
]

bear_hist = trade_signals[
    trade_signals["signal"] == "BEARISH"
]

bull_accuracy = (
    bull_hist["correct"].mean() * 100
    if not bull_hist.empty else 0.0
)

bear_accuracy = (
    bear_hist["correct"].mean() * 100
    if not bear_hist.empty else 0.0
)

print(f"Bullish 30m accuracy: {bull_accuracy:.1f}%")
print(f"Bearish 30m accuracy: {bear_accuracy:.1f}%")

print("\nBASELINE COMPARISON")

BASELINE = 50.0

edge30 = historical_accuracy - BASELINE
edge60 = accuracy60 - BASELINE

print(f"Random baseline:       {BASELINE:.1f}%")
print(f"30m strategy accuracy: {historical_accuracy:.1f}%")
print(f"30m edge vs baseline:  {edge30:+.1f}%")
print(f"60m strategy accuracy: {accuracy60:.1f}%")
print(f"60m edge vs baseline:  {edge60:+.1f}%")

print("\nRESEARCH VERDICT")

if historical_accuracy >= 55 and accuracy60 >= 55:
    research_verdict = "PROMISING"
elif historical_accuracy >= 52 or accuracy60 >= 52:
    research_verdict = "MIXED"
else:
    research_verdict = "WEAK"

print(f"Verdict: {research_verdict}")
print("NOTE: This small sample is NOT proof of profitability.")

research_file = Path("spy_sentinel_research_summary.csv")

research_row = pd.DataFrame([{
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "bars_tested_30m": len(hist_df),
    "signals_30m": len(trade_signals),
    "accuracy_30m": round(historical_accuracy, 2),
    "accuracy_60m": round(accuracy60, 2),
    "bull_accuracy_30m": round(bull_accuracy, 2),
    "bear_accuracy_30m": round(bear_accuracy, 2),
    "edge_30m": round(edge30, 2),
    "edge_60m": round(edge60, 2),
    "verdict": research_verdict,
}])

if research_file.exists():
    research_row.to_csv(
        research_file,
        mode="a",
        header=False,
        index=False
    )
else:
    research_row.to_csv(research_file, index=False)

print(f"Research summary saved to: {research_file}")

print("\nV2.3 MULTI-HORIZON RESEARCH")

research_bars = bars.copy()

HORIZONS = {
    "15m": 3,
    "30m": 6,
    "60m": 12,
    "90m": 18,
}

for label, shift_bars in HORIZONS.items():
    research_bars[f"future_return_{label}"] = (
        research_bars["close"].shift(-shift_bars)
        / research_bars["close"]
        - 1
    )

research_signals = []

for idx, row in research_bars.iterrows():

    if pd.isna(row.get("rsi14")):
        continue

    b = 0
    s = 0

    if row["close"] > row["ema9"]:
        b += 1
    else:
        s += 1

    if row["ema9"] > row["ema21"]:
        b += 1
    else:
        s += 1

    if 52 <= row["rsi14"] <= 70:
        b += 1
    elif 30 <= row["rsi14"] <= 48:
        s += 1

    if b >= 3:
        sig = "BULLISH"
    elif s >= 3:
        sig = "BEARISH"
    else:
        sig = "NO TRADE"

    record = {
        "timestamp": idx,
        "signal": sig
    }

    for label in HORIZONS:
        record[f"return_{label}"] = row[
            f"future_return_{label}"
        ]

    research_signals.append(record)

multi_df = pd.DataFrame(research_signals)

print("\nHORIZON ACCURACY")

horizon_results = []

for label in HORIZONS:

    column = f"return_{label}"

    sample = multi_df[
        multi_df["signal"].isin(["BULLISH", "BEARISH"])
    ].dropna(subset=[column]).copy()

    if sample.empty:
        continue

    sample["correct"] = (
        (
            (sample["signal"] == "BULLISH")
            & (sample[column] > 0)
        )
        |
        (
            (sample["signal"] == "BEARISH")
            & (sample[column] < 0)
        )
    )

    accuracy = sample["correct"].mean() * 100

    horizon_results.append({
        "horizon": label,
        "signals": len(sample),
        "accuracy": accuracy,
        "edge": accuracy - 50
    })

    print(
        f"{label}: {accuracy:.1f}% "
        f"({len(sample)} signals, "
        f"edge {accuracy - 50:+.1f}%)"
    )

print("\nAVERAGE FORWARD RETURNS")

for label in HORIZONS:

    column = f"return_{label}"

    sample = multi_df.dropna(subset=[column])

    bull = sample[sample["signal"] == "BULLISH"]
    bear = sample[sample["signal"] == "BEARISH"]

    bull_return = (
        bull[column].mean() * 100
        if not bull.empty else 0
    )

    bear_return = (
        bear[column].mean() * 100
        if not bear.empty else 0
    )

    print(
        f"{label} | Bull forward return: "
        f"{bull_return:+.3f}% | "
        f"Bear forward return: {bear_return:+.3f}%"
    )

print("\nBEST CURRENT HORIZON")

results_df = pd.DataFrame(horizon_results)

if not results_df.empty:

    best_row = results_df.sort_values(
        "accuracy",
        ascending=False
    ).iloc[0]

    best_horizon = best_row["horizon"]
    best_accuracy = float(best_row["accuracy"])
    best_edge = float(best_row["edge"])

    print(f"Best horizon:  {best_horizon}")
    print(f"Best accuracy: {best_accuracy:.1f}%")
    print(f"Best edge:     {best_edge:+.1f}%")

else:

    best_horizon = "NONE"
    best_accuracy = 0
    best_edge = -50

    print("No usable research results.")

print("\nV2.3 RESEARCH SAFETY VERDICT")

if best_accuracy >= 55 and best_edge >= 5:
    v23_verdict = "WORTH FURTHER TESTING"
else:
    v23_verdict = "STRATEGY NEEDS IMPROVEMENT"

print(f"Verdict: {v23_verdict}")

print("IMPORTANT:")
print("- No thresholds changed to improve these results")
print("- No paper order was submitted")
print("- No live order was submitted")

multi_results_file = Path(
    "spy_sentinel_multi_horizon_results.csv"
)

if not results_df.empty:
    results_df["timestamp_utc"] = (
        datetime.now(timezone.utc).isoformat()
    )

    results_df.to_csv(
        multi_results_file,
        index=False
    )

print(
    f"Multi-horizon results saved to: "
    f"{multi_results_file}"
)

print("\nV2.4 EXTENDED RESEARCH DATA")

research_end = datetime.now(timezone.utc)
research_start = research_end - timedelta(days=60)

research_request = StockBarsRequest(
    symbol_or_symbols=["SPY"],
    timeframe=TimeFrame(5, TimeFrameUnit.Minute),
    start=research_start,
    end=research_end,
    feed=DataFeed.IEX,
)

research60 = data.get_stock_bars(research_request).df

if isinstance(research60.index, pd.MultiIndex):
    research60 = research60.xs("SPY")

research60 = research60.sort_index().copy()

print(f"60-day bars loaded: {len(research60)}")

research60["ema9"] = (
    research60["close"]
    .ewm(span=9, adjust=False)
    .mean()
)

research60["ema21"] = (
    research60["close"]
    .ewm(span=21, adjust=False)
    .mean()
)

r_delta = research60["close"].diff()
r_gain = r_delta.clip(lower=0)
r_loss = -r_delta.clip(upper=0)

r_avg_gain = r_gain.rolling(14).mean()
r_avg_loss = r_loss.rolling(14).mean()

r_rs = r_avg_gain / r_avg_loss.replace(0, np.nan)

research60["rsi14"] = (
    100 - (100 / (1 + r_rs))
)

research60["typical"] = (
    research60["high"]
    + research60["low"]
    + research60["close"]
) / 3

research60["vwap"] = (
    (research60["typical"] * research60["volume"]).cumsum()
    / research60["volume"].cumsum()
)

research60["avg_volume20"] = (
    research60["volume"].rolling(20).mean()
)

research60["volume_ratio"] = (
    research60["volume"]
    / research60["avg_volume20"]
)

print("Extended indicators calculated")

print("\nCHRONOLOGICAL TRAIN / TEST SPLIT")

research60 = research60.dropna().copy()

split_index = int(len(research60) * 0.70)

train60 = research60.iloc[:split_index].copy()
test60_holdout = research60.iloc[split_index:].copy()

print(f"Training bars: {len(train60)}")
print(f"Holdout bars:  {len(test60_holdout)}")
print("Holdout data was NOT used to choose parameters")

def classify_signal(row):

    bull = 0
    bear = 0

    if row["close"] > row["ema9"]:
        bull += 1
    else:
        bear += 1

    if row["ema9"] > row["ema21"]:
        bull += 1
    else:
        bear += 1

    if 52 <= row["rsi14"] <= 70:
        bull += 1
    elif 30 <= row["rsi14"] <= 48:
        bear += 1

    if bull >= 3:
        return "BULLISH"

    if bear >= 3:
        return "BEARISH"

    return "NO TRADE"


test60_holdout["signal"] = (
    test60_holdout.apply(
        classify_signal,
        axis=1
    )
)

print("Holdout signals generated")

print("\nV2.4 HOLDOUT TEST")

HOLDOUT_HORIZONS = {
    "15m": 3,
    "30m": 6,
    "60m": 12,
    "90m": 18,
}

holdout_results = []

for label, shift_count in HOLDOUT_HORIZONS.items():

    future_col = f"future_{label}"

    test60_holdout[future_col] = (
        test60_holdout["close"].shift(-shift_count)
        / test60_holdout["close"]
        - 1
    )

    sample = test60_holdout[
        test60_holdout["signal"].isin(
            ["BULLISH", "BEARISH"]
        )
    ].dropna(subset=[future_col]).copy()

    sample["correct"] = (
        (
            (sample["signal"] == "BULLISH")
            & (sample[future_col] > 0)
        )
        |
        (
            (sample["signal"] == "BEARISH")
            & (sample[future_col] < 0)
        )
    )

    accuracy = (
        sample["correct"].mean() * 100
        if not sample.empty
        else 0
    )

    holdout_results.append({
        "horizon": label,
        "signals": len(sample),
        "accuracy": accuracy,
        "edge": accuracy - 50,
    })

    print(
        f"{label}: {accuracy:.1f}% | "
        f"{len(sample)} signals | "
        f"edge {accuracy - 50:+.1f}%"
    )

print("\nFILTERED HOLDOUT TEST")

filtered = test60_holdout[
    test60_holdout["signal"].isin(
        ["BULLISH", "BEARISH"]
    )
].copy()

filtered["vwap_match"] = (
    (
        (filtered["signal"] == "BULLISH")
        & (filtered["close"] > filtered["vwap"])
    )
    |
    (
        (filtered["signal"] == "BEARISH")
        & (filtered["close"] < filtered["vwap"])
    )
)

filtered["volume_pass"] = (
    filtered["volume_ratio"] >= 1.0
)

filtered = filtered[
    filtered["vwap_match"]
    & filtered["volume_pass"]
]

print(f"Signals after VWAP + volume filters: {len(filtered)}")

filtered_results = []

for label, shift_count in HOLDOUT_HORIZONS.items():

    future_col = f"filtered_future_{label}"

    filtered[future_col] = (
        filtered["close"].shift(-shift_count)
        / filtered["close"]
        - 1
    )

    sample = filtered.dropna(
        subset=[future_col]
    ).copy()

    sample["correct"] = (
        (
            (sample["signal"] == "BULLISH")
            & (sample[future_col] > 0)
        )
        |
        (
            (sample["signal"] == "BEARISH")
            & (sample[future_col] < 0)
        )
    )

    accuracy = (
        sample["correct"].mean() * 100
        if not sample.empty
        else 0
    )

    filtered_results.append({
        "horizon": label,
        "signals": len(sample),
        "accuracy": accuracy,
        "edge": accuracy - 50,
    })

    print(
        f"Filtered {label}: "
        f"{accuracy:.1f}% | "
        f"{len(sample)} signals | "
        f"edge {accuracy - 50:+.1f}%"
    )

print("\nV2.4 OUT-OF-SAMPLE VERDICT")

holdout_df = pd.DataFrame(holdout_results)
filtered_df = pd.DataFrame(filtered_results)

best_raw = holdout_df.sort_values(
    "accuracy",
    ascending=False
).iloc[0]

best_filtered = filtered_df.sort_values(
    "accuracy",
    ascending=False
).iloc[0]

print(
    f"Best raw: {best_raw['horizon']} "
    f"{best_raw['accuracy']:.1f}% "
    f"({int(best_raw['signals'])} signals)"
)

print(
    f"Best filtered: {best_filtered['horizon']} "
    f"{best_filtered['accuracy']:.1f}% "
    f"({int(best_filtered['signals'])} signals)"
)

if (
    best_filtered["accuracy"] >= 55
    and best_filtered["signals"] >= 30
):
    oos_verdict = "PROMISING — CONTINUE VALIDATION"
else:
    oos_verdict = "NOT PROVEN — KEEP RESEARCHING"

print(f"Verdict: {oos_verdict}")
print("PAPER ORDER SYSTEM: LOCKED")
print("LIVE ORDER SYSTEM: LOCKED")

print("\nV2.5 RESEARCH CORRECTION")

clean = research60.copy()

clean.index = pd.to_datetime(clean.index, utc=True)

clean["time_et"] = clean.index.tz_convert("America/New_York")
clean["date_et"] = clean["time_et"].dt.date
clean["clock_et"] = clean["time_et"].dt.time

from datetime import time

clean = clean[
    (clean["clock_et"] >= time(9, 30))
    & (clean["clock_et"] <= time(16, 0))
].copy()

print(f"Regular-session bars: {len(clean)}")

clean["ema9"] = clean["close"].ewm(
    span=9,
    adjust=False
).mean()

clean["ema21"] = clean["close"].ewm(
    span=21,
    adjust=False
).mean()

delta_c = clean["close"].diff()

gain_c = delta_c.clip(lower=0)
loss_c = -delta_c.clip(upper=0)

avg_gain_c = gain_c.rolling(14).mean()
avg_loss_c = loss_c.rolling(14).mean()

rs_c = avg_gain_c / avg_loss_c.replace(0, np.nan)

clean["rsi14"] = 100 - (100 / (1 + rs_c))

print("Core indicators recalculated")

clean["typical_price"] = (
    clean["high"]
    + clean["low"]
    + clean["close"]
) / 3

clean["tp_volume"] = (
    clean["typical_price"] * clean["volume"]
)

clean["daily_cum_tp_volume"] = (
    clean.groupby("date_et")["tp_volume"].cumsum()
)

clean["daily_cum_volume"] = (
    clean.groupby("date_et")["volume"].cumsum()
)

clean["vwap"] = (
    clean["daily_cum_tp_volume"]
    / clean["daily_cum_volume"]
)

clean["avg_volume20"] = clean["volume"].rolling(20).mean()

clean["volume_ratio"] = (
    clean["volume"]
    / clean["avg_volume20"]
)

print("Daily-reset VWAP calculated")

CORRECT_HORIZONS = {
    "15m": 3,
    "30m": 6,
    "60m": 12,
    "90m": 18,
}

for label, bars_forward in CORRECT_HORIZONS.items():

    future_price = clean["close"].shift(-bars_forward)

    same_day = (
        clean["date_et"]
        == clean["date_et"].shift(-bars_forward)
    )

    clean[f"future_return_{label}"] = np.where(
        same_day,
        future_price / clean["close"] - 1,
        np.nan
    )

print("True candle-based future returns calculated")

clean = clean.dropna(
    subset=["ema9", "ema21", "rsi14", "vwap", "volume_ratio"]
).copy()

clean["signal"] = clean.apply(
    classify_signal,
    axis=1
)

signal_rows = clean[
    clean["signal"].isin(["BULLISH", "BEARISH"])
].copy()

signal_rows["vwap_match"] = (
    (
        (signal_rows["signal"] == "BULLISH")
        & (signal_rows["close"] > signal_rows["vwap"])
    )
    |
    (
        (signal_rows["signal"] == "BEARISH")
        & (signal_rows["close"] < signal_rows["vwap"])
    )
)

signal_rows["volume_pass"] = (
    signal_rows["volume_ratio"] >= 1.0
)

correct_filtered = signal_rows[
    signal_rows["vwap_match"]
    & signal_rows["volume_pass"]
].copy()

print(f"Corrected filtered signals: {len(correct_filtered)}")

split_time = clean.index[int(len(clean) * 0.70)]

correct_holdout = correct_filtered[
    correct_filtered.index >= split_time
].copy()

print(f"Corrected holdout signals: {len(correct_holdout)}")
print(f"Holdout begins: {split_time}")

print("\nCORRECTED OUT-OF-SAMPLE RESULTS")

correct_results = []

for label in CORRECT_HORIZONS:

    col = f"future_return_{label}"

    sample = correct_holdout.dropna(
        subset=[col]
    ).copy()

    sample["correct"] = (
        (
            (sample["signal"] == "BULLISH")
            & (sample[col] > 0)
        )
        |
        (
            (sample["signal"] == "BEARISH")
            & (sample[col] < 0)
        )
    )

    accuracy = (
        sample["correct"].mean() * 100
        if len(sample)
        else 0.0
    )

    correct_results.append({
        "horizon": label,
        "signals": len(sample),
        "accuracy": accuracy,
        "edge": accuracy - 50,
    })

    print(
        f"{label}: {accuracy:.1f}% | "
        f"{len(sample)} signals | "
        f"edge {accuracy - 50:+.1f}%"
    )

correct_df = pd.DataFrame(correct_results)

best_correct = correct_df.sort_values(
    "accuracy",
    ascending=False
).iloc[0]

print("\nV2.5 CORRECTED VERDICT")

print(
    f"Best horizon: {best_correct['horizon']}"
)

print(
    f"Accuracy: {best_correct['accuracy']:.1f}%"
)

print(
    f"Signals: {int(best_correct['signals'])}"
)

print(
    f"Edge: {best_correct['edge']:+.1f}%"
)

if (
    best_correct["accuracy"] >= 55
    and best_correct["signals"] >= 30
):
    corrected_verdict = "PROMISING"
else:
    corrected_verdict = "NOT PROVEN"

print(f"Corrected verdict: {corrected_verdict}")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

print("\nV2.6 WALK-FORWARD STABILITY TEST")

def evaluate_period(frame, period_name):

    rows = []

    for label in CORRECT_HORIZONS:

        col = f"future_return_{label}"

        sample = frame.dropna(subset=[col]).copy()

        if sample.empty:
            accuracy = 0.0
        else:
            sample["correct"] = (
                (
                    (sample["signal"] == "BULLISH")
                    & (sample[col] > 0)
                )
                |
                (
                    (sample["signal"] == "BEARISH")
                    & (sample[col] < 0)
                )
            )

            accuracy = sample["correct"].mean() * 100

        rows.append({
            "period": period_name,
            "horizon": label,
            "signals": len(sample),
            "accuracy": accuracy,
            "edge": accuracy - 50,
        })

    return rows

eligible = correct_filtered.sort_index().copy()

n = len(eligible)

cut1 = int(n * 0.40)
cut2 = int(n * 0.60)
cut3 = int(n * 0.80)

period1 = eligible.iloc[cut1:cut2].copy()
period2 = eligible.iloc[cut2:cut3].copy()
period3 = eligible.iloc[cut3:].copy()

walk_results = []

walk_results += evaluate_period(period1, "FOLD_1")
walk_results += evaluate_period(period2, "FOLD_2")
walk_results += evaluate_period(period3, "FOLD_3")

walk_df = pd.DataFrame(walk_results)

print(f"Fold 1 signals: {len(period1)}")
print(f"Fold 2 signals: {len(period2)}")
print(f"Fold 3 signals: {len(period3)}")

print("\nWALK-FORWARD RESULTS")

for _, row in walk_df.iterrows():

    print(
        f"{row['period']} {row['horizon']}: "
        f"{row['accuracy']:.1f}% | "
        f"{int(row['signals'])} signals | "
        f"edge {row['edge']:+.1f}%"
    )

print("\nHORIZON STABILITY")

stability_rows = []

for horizon in CORRECT_HORIZONS:

    h = walk_df[
        walk_df["horizon"] == horizon
    ].copy()

    mean_accuracy = h["accuracy"].mean()
    minimum_accuracy = h["accuracy"].min()
    maximum_accuracy = h["accuracy"].max()
    total_signals = int(h["signals"].sum())

    stability_rows.append({
        "horizon": horizon,
        "mean_accuracy": mean_accuracy,
        "minimum_accuracy": minimum_accuracy,
        "maximum_accuracy": maximum_accuracy,
        "total_signals": total_signals,
    })

    print(
        f"{horizon}: mean {mean_accuracy:.1f}% | "
        f"worst {minimum_accuracy:.1f}% | "
        f"best {maximum_accuracy:.1f}% | "
        f"{total_signals} signals"
    )

stability_df = pd.DataFrame(stability_rows)

print("\nDIRECTION STABILITY")

direction_rows = []

for period_name, frame in [
    ("FOLD_1", period1),
    ("FOLD_2", period2),
    ("FOLD_3", period3),
]:

    col = "future_return_15m"

    sample = frame.dropna(subset=[col]).copy()

    for direction in ["BULLISH", "BEARISH"]:

        d = sample[
            sample["signal"] == direction
        ].copy()

        if not d.empty:

            if direction == "BULLISH":
                correct = d[col] > 0
            else:
                correct = d[col] < 0

            acc = correct.mean() * 100

        else:
            acc = 0.0

        direction_rows.append({
            "period": period_name,
            "direction": direction,
            "signals": len(d),
            "accuracy": acc,
        })

        print(
            f"{period_name} {direction}: "
            f"{acc:.1f}% | {len(d)} signals"
        )

print("\nV2.6 STABILITY VERDICT")

best_stable = stability_df.sort_values(
    ["minimum_accuracy", "mean_accuracy"],
    ascending=False
).iloc[0]

stable_enough = (
    best_stable["mean_accuracy"] >= 55
    and best_stable["minimum_accuracy"] >= 50
    and best_stable["total_signals"] >= 30
)

print(f"Best horizon:       {best_stable['horizon']}")
print(f"Mean accuracy:      {best_stable['mean_accuracy']:.1f}%")
print(f"Worst fold:         {best_stable['minimum_accuracy']:.1f}%")
print(f"Total signals:      {int(best_stable['total_signals'])}")

if stable_enough:
    stability_verdict = "PROMISING AND REASONABLY STABLE"
else:
    stability_verdict = "NOT STABLE ENOUGH"

print(f"Verdict:            {stability_verdict}")
print("PAPER TRADING:      LOCKED")
print("LIVE TRADING:       LOCKED")

walk_file = Path(
    "spy_sentinel_walk_forward_results.csv"
)

walk_df.to_csv(
    walk_file,
    index=False
)

stability_file = Path(
    "spy_sentinel_stability_summary.csv"
)

stability_df.to_csv(
    stability_file,
    index=False
)

print(f"Walk-forward results saved to: {walk_file}")
print(f"Stability summary saved to: {stability_file}")

print("\nV2.7 TIME-OF-DAY RESEARCH")

tod = correct_filtered.copy()

tod["hour_et"] = (
    tod.index
    .tz_convert("America/New_York")
    .hour
)

tod["minute_et"] = (
    tod.index
    .tz_convert("America/New_York")
    .minute
)

tod["minutes_et"] = (
    tod["hour_et"] * 60
    + tod["minute_et"]
)

def session_bucket(minutes):
    if 570 <= minutes < 660:
        return "MORNING"
    elif 660 <= minutes < 810:
        return "MIDDAY"
    elif 810 <= minutes <= 945:
        return "AFTERNOON"
    return "OTHER"

tod["session_bucket"] = tod["minutes_et"].apply(session_bucket)

print(tod["session_bucket"].value_counts())

print("\n15-MINUTE ACCURACY BY SESSION")

session_results = []

for session_name in ["MORNING", "MIDDAY", "AFTERNOON"]:

    sample = tod[
        tod["session_bucket"] == session_name
    ].dropna(
        subset=["future_return_15m"]
    ).copy()

    sample["correct"] = (
        (
            (sample["signal"] == "BULLISH")
            & (sample["future_return_15m"] > 0)
        )
        |
        (
            (sample["signal"] == "BEARISH")
            & (sample["future_return_15m"] < 0)
        )
    )

    accuracy = (
        sample["correct"].mean() * 100
        if not sample.empty
        else 0.0
    )

    session_results.append({
        "session": session_name,
        "signals": len(sample),
        "accuracy": accuracy,
        "edge": accuracy - 50,
    })

    print(
        f"{session_name}: {accuracy:.1f}% | "
        f"{len(sample)} signals | "
        f"edge {accuracy - 50:+.1f}%"
    )

print("\nDIRECTION PERFORMANCE")

direction_results = []

for direction in ["BULLISH", "BEARISH"]:

    sample = tod[
        tod["signal"] == direction
    ].dropna(
        subset=["future_return_15m"]
    ).copy()

    if direction == "BULLISH":
        correct = sample["future_return_15m"] > 0
    else:
        correct = sample["future_return_15m"] < 0

    accuracy = (
        correct.mean() * 100
        if len(sample)
        else 0.0
    )

    direction_results.append({
        "direction": direction,
        "signals": len(sample),
        "accuracy": accuracy,
        "edge": accuracy - 50,
    })

    print(
        f"{direction}: {accuracy:.1f}% | "
        f"{len(sample)} signals | "
        f"edge {accuracy - 50:+.1f}%"
    )

print("\nSESSION + DIRECTION BREAKDOWN")

combo_results = []

for session_name in ["MORNING", "MIDDAY", "AFTERNOON"]:

    for direction in ["BULLISH", "BEARISH"]:

        sample = tod[
            (tod["session_bucket"] == session_name)
            & (tod["signal"] == direction)
        ].dropna(
            subset=["future_return_15m"]
        ).copy()

        if direction == "BULLISH":
            correct = sample["future_return_15m"] > 0
        else:
            correct = sample["future_return_15m"] < 0

        accuracy = (
            correct.mean() * 100
            if len(sample)
            else 0.0
        )

        combo_results.append({
            "session": session_name,
            "direction": direction,
            "signals": len(sample),
            "accuracy": accuracy,
            "edge": accuracy - 50,
        })

        print(
            f"{session_name} {direction}: "
            f"{accuracy:.1f}% | "
            f"{len(sample)} signals"
        )

print("\nMINIMUM-SAMPLE FILTER")

combo_df = pd.DataFrame(combo_results)

usable_combos = combo_df[
    combo_df["signals"] >= 20
].copy()

if not usable_combos.empty:

    best_combo = usable_combos.sort_values(
        "accuracy",
        ascending=False
    ).iloc[0]

    print(
        f"Best adequately sampled segment: "
        f"{best_combo['session']} "
        f"{best_combo['direction']}"
    )

    print(
        f"Accuracy: {best_combo['accuracy']:.1f}%"
    )

    print(
        f"Signals: {int(best_combo['signals'])}"
    )

else:
    best_combo = None
    print("No segment has at least 20 signals.")

print("\nV2.7 SEGMENT VERDICT")

if (
    best_combo is not None
    and best_combo["accuracy"] >= 55
    and best_combo["signals"] >= 20
):
    segment_verdict = "SEGMENT WORTH VALIDATING"
else:
    segment_verdict = "NO SEGMENT PROVEN"

print(f"Verdict: {segment_verdict}")
print("NO STRATEGY RULES WERE CHANGED")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

pd.DataFrame(session_results).to_csv(
    "spy_sentinel_session_results.csv",
    index=False
)

pd.DataFrame(direction_results).to_csv(
    "spy_sentinel_direction_results.csv",
    index=False
)

combo_df.to_csv(
    "spy_sentinel_session_direction_results.csv",
    index=False
)

print("Segment research files saved")

print("\nV2.8 MIDDAY BULLISH VALIDATION")

midday_bull = tod[
    (tod["session_bucket"] == "MIDDAY")
    & (tod["signal"] == "BULLISH")
].copy()

midday_bull = midday_bull.dropna(
    subset=["future_return_15m"]
)

print(f"Total midday bullish signals: {len(midday_bull)}")

n_mb = len(midday_bull)

mb_cut1 = int(n_mb * 0.40)
mb_cut2 = int(n_mb * 0.60)
mb_cut3 = int(n_mb * 0.80)

mb_fold1 = midday_bull.iloc[mb_cut1:mb_cut2].copy()
mb_fold2 = midday_bull.iloc[mb_cut2:mb_cut3].copy()
mb_fold3 = midday_bull.iloc[mb_cut3:].copy()

print(f"Fold 1: {len(mb_fold1)} signals")
print(f"Fold 2: {len(mb_fold2)} signals")
print(f"Fold 3: {len(mb_fold3)} signals")

print("\nMIDDAY BULLISH FOLD ACCURACY")

mb_results = []

for name, frame in [
    ("FOLD_1", mb_fold1),
    ("FOLD_2", mb_fold2),
    ("FOLD_3", mb_fold3),
]:

    if frame.empty:
        accuracy = 0.0
    else:
        correct = frame["future_return_15m"] > 0
        accuracy = correct.mean() * 100

    mb_results.append({
        "fold": name,
        "signals": len(frame),
        "accuracy": accuracy,
        "edge": accuracy - 50,
    })

    print(
        f"{name}: {accuracy:.1f}% | "
        f"{len(frame)} signals | "
        f"edge {accuracy - 50:+.1f}%"
    )

mb_df = pd.DataFrame(mb_results)

mb_mean = mb_df["accuracy"].mean()
mb_worst = mb_df["accuracy"].min()
mb_best = mb_df["accuracy"].max()
mb_signals = int(mb_df["signals"].sum())

print("\nMIDDAY BULLISH STABILITY")

print(f"Mean accuracy: {mb_mean:.1f}%")
print(f"Worst fold:    {mb_worst:.1f}%")
print(f"Best fold:     {mb_best:.1f}%")
print(f"Test signals:  {mb_signals}")

print("\nMIDDAY BULLISH FORWARD RETURN")

avg_return = (
    midday_bull["future_return_15m"].mean() * 100
    if not midday_bull.empty
    else 0.0
)

median_return = (
    midday_bull["future_return_15m"].median() * 100
    if not midday_bull.empty
    else 0.0
)

print(f"Average 15m return: {avg_return:+.3f}%")
print(f"Median 15m return:  {median_return:+.3f}%")

print("\nV2.8 VALIDATION VERDICT")

mb_valid = (
    mb_mean >= 55
    and mb_worst >= 50
    and mb_signals >= 30
    and avg_return > 0
)

if mb_valid:
    mb_verdict = "MIDDAY BULLISH PASSES FIRST VALIDATION"
else:
    mb_verdict = "MIDDAY BULLISH NOT YET PROVEN"

print(f"Verdict: {mb_verdict}")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

mb_df.to_csv(
    "spy_sentinel_midday_bullish_folds.csv",
    index=False
)

summary_mb = pd.DataFrame([{
    "total_signals": len(midday_bull),
    "test_signals": mb_signals,
    "mean_accuracy": round(mb_mean, 2),
    "worst_fold": round(mb_worst, 2),
    "best_fold": round(mb_best, 2),
    "avg_return_15m": round(avg_return, 4),
    "median_return_15m": round(median_return, 4),
    "validated": mb_valid,
    "verdict": mb_verdict,
}])

summary_mb.to_csv(
    "spy_sentinel_midday_bullish_summary.csv",
    index=False
)

print("Midday bullish validation files saved")
