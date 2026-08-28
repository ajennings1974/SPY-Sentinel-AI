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

print("\nV2.9 INDEPENDENT VALIDATION PERIOD")

independent_end = datetime.now(timezone.utc) - timedelta(days=60)
independent_start = independent_end - timedelta(days=90)

independent_request = StockBarsRequest(
    symbol_or_symbols=["SPY"],
    timeframe=TimeFrame(5, TimeFrameUnit.Minute),
    start=independent_start,
    end=independent_end,
    feed=DataFeed.IEX,
)

independent = data.get_stock_bars(independent_request).df

if isinstance(independent.index, pd.MultiIndex):
    independent = independent.xs("SPY")

independent = independent.sort_index().copy()

print(f"Independent bars loaded: {len(independent)}")
print(f"Period start: {independent_start.date()}")
print(f"Period end:   {independent_end.date()}")

independent.index = pd.to_datetime(
    independent.index,
    utc=True
)

independent["time_et"] = (
    independent.index.tz_convert("America/New_York")
)

independent["date_et"] = independent["time_et"].dt.date
independent["clock_et"] = independent["time_et"].dt.time

from datetime import time

independent = independent[
    (independent["clock_et"] >= time(9, 30))
    & (independent["clock_et"] <= time(16, 0))
].copy()

print(f"Regular-session independent bars: {len(independent)}")

independent["ema9"] = (
    independent["close"]
    .ewm(span=9, adjust=False)
    .mean()
)

independent["ema21"] = (
    independent["close"]
    .ewm(span=21, adjust=False)
    .mean()
)

i_delta = independent["close"].diff()
i_gain = i_delta.clip(lower=0)
i_loss = -i_delta.clip(upper=0)

i_avg_gain = i_gain.rolling(14).mean()
i_avg_loss = i_loss.rolling(14).mean()

i_rs = i_avg_gain / i_avg_loss.replace(0, np.nan)

independent["rsi14"] = (
    100 - (100 / (1 + i_rs))
)

print("Independent indicators calculated")

independent["typical_price"] = (
    independent["high"]
    + independent["low"]
    + independent["close"]
) / 3

independent["tp_volume"] = (
    independent["typical_price"]
    * independent["volume"]
)

independent["cum_tpv"] = (
    independent.groupby("date_et")["tp_volume"].cumsum()
)

independent["cum_volume"] = (
    independent.groupby("date_et")["volume"].cumsum()
)

independent["vwap"] = (
    independent["cum_tpv"]
    / independent["cum_volume"]
)

independent["avg_volume20"] = (
    independent["volume"].rolling(20).mean()
)

independent["volume_ratio"] = (
    independent["volume"]
    / independent["avg_volume20"]
)

print("Independent daily VWAP and volume calculated")

independent["future_return_15m"] = np.where(
    independent["date_et"]
    == independent["date_et"].shift(-3),
    independent["close"].shift(-3)
    / independent["close"]
    - 1,
    np.nan
)

independent = independent.dropna(
    subset=[
        "ema9",
        "ema21",
        "rsi14",
        "vwap",
        "volume_ratio",
    ]
).copy()

independent["signal"] = independent.apply(
    classify_signal,
    axis=1
)

print("Independent signals generated")

independent["minutes_et"] = (
    independent["time_et"].dt.hour * 60
    + independent["time_et"].dt.minute
)

independent_midday_bull = independent[
    (independent["minutes_et"] >= 660)
    & (independent["minutes_et"] < 810)
    & (independent["signal"] == "BULLISH")
    & (independent["close"] > independent["vwap"])
    & (independent["volume_ratio"] >= 1.0)
].dropna(
    subset=["future_return_15m"]
).copy()

print(
    f"Independent MIDDAY BULLISH signals: "
    f"{len(independent_midday_bull)}"
)

print("\nINDEPENDENT MIDDAY BULLISH RESULTS")

independent_wins = (
    independent_midday_bull["future_return_15m"] > 0
)

independent_accuracy = (
    independent_wins.mean() * 100
    if len(independent_midday_bull)
    else 0.0
)

independent_avg_return = (
    independent_midday_bull["future_return_15m"].mean() * 100
    if len(independent_midday_bull)
    else 0.0
)

independent_median_return = (
    independent_midday_bull["future_return_15m"].median() * 100
    if len(independent_midday_bull)
    else 0.0
)

print(f"Signals:        {len(independent_midday_bull)}")
print(f"Accuracy:       {independent_accuracy:.1f}%")
print(f"Average return: {independent_avg_return:+.3f}%")
print(f"Median return:  {independent_median_return:+.3f}%")

print("\nV2.9 INDEPENDENT VERDICT")

independent_pass = (
    len(independent_midday_bull) >= 30
    and independent_accuracy >= 55
    and independent_avg_return > 0
)

if independent_pass:
    independent_verdict = "PASSES SECOND VALIDATION"
else:
    independent_verdict = "DOES NOT PASS SECOND VALIDATION"

print(f"Verdict: {independent_verdict}")
print("RULES WERE NOT CHANGED FOR THIS TEST")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

independent_summary = pd.DataFrame([{
    "signals": len(independent_midday_bull),
    "accuracy": round(independent_accuracy, 2),
    "average_return_15m": round(independent_avg_return, 4),
    "median_return_15m": round(independent_median_return, 4),
    "passed": independent_pass,
    "verdict": independent_verdict,
}])

independent_summary.to_csv(
    "spy_sentinel_independent_validation.csv",
    index=False
)

print("Independent validation saved")

print("\nV3.0 STATISTICAL RELIABILITY CHECK")

n_ind = len(independent_midday_bull)
wins_ind = int(
    (independent_midday_bull["future_return_15m"] > 0).sum()
)

p_hat = wins_ind / n_ind if n_ind else 0.0

print(f"Signals: {n_ind}")
print(f"Wins:    {wins_ind}")
print(f"Win rate:{p_hat * 100:.2f}%")

print("\n95% WILSON CONFIDENCE INTERVAL")

if n_ind > 0:

    z = 1.96

    denominator = 1 + (z ** 2 / n_ind)

    center = (
        p_hat
        + z ** 2 / (2 * n_ind)
    ) / denominator

    margin = (
        z
        * np.sqrt(
            (
                p_hat * (1 - p_hat) / n_ind
                + z ** 2 / (4 * n_ind ** 2)
            )
        )
        / denominator
    )

    ci_low = center - margin
    ci_high = center + margin

else:
    ci_low = 0
    ci_high = 0

print(f"Lower bound: {ci_low * 100:.2f}%")
print(f"Upper bound: {ci_high * 100:.2f}%")
print(f"Contains 50%: {ci_low <= 0.50 <= ci_high}")

print("\nBOOTSTRAP RETURN TEST")

returns = (
    independent_midday_bull["future_return_15m"]
    .dropna()
    .to_numpy()
)

rng = np.random.default_rng(42)

bootstrap_means = []

if len(returns) > 0:

    for _ in range(5000):

        sample = rng.choice(
            returns,
            size=len(returns),
            replace=True
        )

        bootstrap_means.append(
            sample.mean()
        )

bootstrap_means = np.array(bootstrap_means)

if len(bootstrap_means) > 0:

    boot_low = np.percentile(
        bootstrap_means,
        2.5
    )

    boot_high = np.percentile(
        bootstrap_means,
        97.5
    )

else:

    boot_low = 0
    boot_high = 0

print(f"Mean return CI low:  {boot_low * 100:+.4f}%")
print(f"Mean return CI high: {boot_high * 100:+.4f}%")
print(f"Contains zero: {boot_low <= 0 <= boot_high}")

print("\nEDGE STRENGTH")

accuracy_edge = (
    independent_accuracy - 50
)

return_edge = (
    independent_avg_return
)

print(f"Accuracy edge:     {accuracy_edge:+.2f}%")
print(f"Avg forward return:{return_edge:+.4f}%")

statistically_clear = (
    ci_low > 0.50
    and boot_low > 0
)

print(f"Statistically clear edge: {statistically_clear}")

print("\nFIRST VS SECOND VALIDATION")

first_accuracy = mb_mean
second_accuracy = independent_accuracy

accuracy_drop = (
    second_accuracy - first_accuracy
)

print(f"First validation mean:  {first_accuracy:.2f}%")
print(f"Second validation:      {second_accuracy:.2f}%")
print(f"Change:                 {accuracy_drop:+.2f}%")

validation_consistent = (
    abs(accuracy_drop) <= 5
    and second_accuracy >= 55
)

print(f"Validation consistent: {validation_consistent}")

print("\nV3.0 RESEARCH GATE")

research_gate_pass = (
    independent_pass
    and statistically_clear
    and validation_consistent
)

if research_gate_pass:
    research_gate_status = "PASS"
else:
    research_gate_status = "FAIL"

print(f"Research gate: {research_gate_status}")

if not independent_pass:
    print("- Independent validation failed")

if not statistically_clear:
    print("- Statistical edge is not clear")

if not validation_consistent:
    print("- Results are not stable across validation periods")

print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

stat_summary = pd.DataFrame([{
    "signals": n_ind,
    "wins": wins_ind,
    "win_rate": round(p_hat * 100, 4),
    "ci_low": round(ci_low * 100, 4),
    "ci_high": round(ci_high * 100, 4),
    "bootstrap_return_low": round(boot_low * 100, 6),
    "bootstrap_return_high": round(boot_high * 100, 6),
    "accuracy_edge": round(accuracy_edge, 4),
    "avg_forward_return": round(return_edge, 6),
    "statistically_clear": statistically_clear,
    "validation_consistent": validation_consistent,
    "research_gate_pass": research_gate_pass,
}])

stat_summary.to_csv(
    "spy_sentinel_statistical_validation.csv",
    index=False
)

print("Statistical validation saved")

print("\nV3.1 MOMENTUM-ALIGNMENT RESEARCH")

momentum_dev = correct_filtered.copy()

momentum_dev["momentum_15m"] = (
    momentum_dev["close"].pct_change(3)
)

momentum_dev["momentum_60m"] = (
    momentum_dev["close"].pct_change(12)
)

# Lag the momentum values one 5-minute bar
# so the test never uses information from the future.
momentum_dev["momentum_15m_lag"] = (
    momentum_dev["momentum_15m"].shift(1)
)

momentum_dev["momentum_60m_lag"] = (
    momentum_dev["momentum_60m"].shift(1)
)

print("Lagged momentum features calculated")

momentum_dev["momentum_match"] = (
    (
        (momentum_dev["signal"] == "BULLISH")
        & (momentum_dev["momentum_15m_lag"] > 0)
        & (momentum_dev["momentum_60m_lag"] > 0)
    )
    |
    (
        (momentum_dev["signal"] == "BEARISH")
        & (momentum_dev["momentum_15m_lag"] < 0)
        & (momentum_dev["momentum_60m_lag"] < 0)
    )
)

matched = momentum_dev[
    momentum_dev["momentum_match"]
].copy()

unmatched = momentum_dev[
    ~momentum_dev["momentum_match"]
].copy()

print(f"Momentum-matched signals:   {len(matched)}")
print(f"Momentum-unmatched signals: {len(unmatched)}")

print("\nMATCHED VS UNMATCHED — 15 MINUTES")

def directional_accuracy(frame, return_col):

    sample = frame.dropna(
        subset=[return_col]
    ).copy()

    if sample.empty:
        return 0.0, 0

    correct = (
        (
            (sample["signal"] == "BULLISH")
            & (sample[return_col] > 0)
        )
        |
        (
            (sample["signal"] == "BEARISH")
            & (sample[return_col] < 0)
        )
    )

    return correct.mean() * 100, len(sample)


matched_acc15, matched_n15 = directional_accuracy(
    matched,
    "future_return_15m"
)

unmatched_acc15, unmatched_n15 = directional_accuracy(
    unmatched,
    "future_return_15m"
)

print(
    f"Matched:   {matched_acc15:.1f}% | "
    f"{matched_n15} signals"
)

print(
    f"Unmatched: {unmatched_acc15:.1f}% | "
    f"{unmatched_n15} signals"
)

print("\nMATCHED PERFORMANCE BY HORIZON")

momentum_results = []

for label in CORRECT_HORIZONS:

    col = f"future_return_{label}"

    accuracy, count = directional_accuracy(
        matched,
        col
    )

    momentum_results.append({
        "horizon": label,
        "signals": count,
        "accuracy": accuracy,
        "edge": accuracy - 50,
    })

    print(
        f"{label}: {accuracy:.1f}% | "
        f"{count} signals | "
        f"edge {accuracy - 50:+.1f}%"
    )

momentum_results_df = pd.DataFrame(
    momentum_results
)

print("\nMOMENTUM RETURN QUALITY")

matched_returns = matched.dropna(
    subset=["future_return_15m"]
).copy()

signed_return = np.where(
    matched_returns["signal"] == "BULLISH",
    matched_returns["future_return_15m"],
    -matched_returns["future_return_15m"]
)

avg_signed_return = (
    float(np.mean(signed_return)) * 100
    if len(signed_return)
    else 0.0
)

median_signed_return = (
    float(np.median(signed_return)) * 100
    if len(signed_return)
    else 0.0
)

print(
    f"Average directional return: "
    f"{avg_signed_return:+.4f}%"
)

print(
    f"Median directional return:  "
    f"{median_signed_return:+.4f}%"
)

print("\nV3.1 DEVELOPMENT VERDICT")

best_momentum = momentum_results_df.sort_values(
    "accuracy",
    ascending=False
).iloc[0]

momentum_candidate = (
    best_momentum["accuracy"] >= 55
    and best_momentum["signals"] >= 30
    and avg_signed_return > 0
)

print(
    f"Best horizon: "
    f"{best_momentum['horizon']}"
)

print(
    f"Best accuracy: "
    f"{best_momentum['accuracy']:.1f}%"
)

print(
    f"Signals: "
    f"{int(best_momentum['signals'])}"
)

print(
    f"Candidate worth independent test: "
    f"{momentum_candidate}"
)

print("THIS IS DEVELOPMENT DATA — NOT FINAL VALIDATION")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

momentum_results_df.to_csv(
    "spy_sentinel_momentum_research.csv",
    index=False
)

momentum_summary = pd.DataFrame([{
    "matched_signals_15m": matched_n15,
    "matched_accuracy_15m": round(matched_acc15, 2),
    "unmatched_signals_15m": unmatched_n15,
    "unmatched_accuracy_15m": round(unmatched_acc15, 2),
    "avg_directional_return": round(avg_signed_return, 5),
    "median_directional_return": round(median_signed_return, 5),
    "candidate": momentum_candidate,
}])

momentum_summary.to_csv(
    "spy_sentinel_momentum_summary.csv",
    index=False
)

print("Momentum research saved")

print("\nV3.2 INDEPENDENT MOMENTUM VALIDATION")

ind_mom = independent.copy()

ind_mom["momentum_15m"] = (
    ind_mom["close"].pct_change(3)
)

ind_mom["momentum_60m"] = (
    ind_mom["close"].pct_change(12)
)

ind_mom["momentum_15m_lag"] = (
    ind_mom["momentum_15m"].shift(1)
)

ind_mom["momentum_60m_lag"] = (
    ind_mom["momentum_60m"].shift(1)
)

print("Independent lagged momentum calculated")

ind_mom["momentum_match"] = (
    (
        (ind_mom["signal"] == "BULLISH")
        & (ind_mom["momentum_15m_lag"] > 0)
        & (ind_mom["momentum_60m_lag"] > 0)
    )
    |
    (
        (ind_mom["signal"] == "BEARISH")
        & (ind_mom["momentum_15m_lag"] < 0)
        & (ind_mom["momentum_60m_lag"] < 0)
    )
)

ind_mom["vwap_match"] = (
    (
        (ind_mom["signal"] == "BULLISH")
        & (ind_mom["close"] > ind_mom["vwap"])
    )
    |
    (
        (ind_mom["signal"] == "BEARISH")
        & (ind_mom["close"] < ind_mom["vwap"])
    )
)

independent_matched = ind_mom[
    ind_mom["momentum_match"]
    & ind_mom["vwap_match"]
    & (ind_mom["volume_ratio"] >= 1.0)
].copy()

print(
    f"Independent matched signals: "
    f"{len(independent_matched)}"
)

independent_matched["future_return_60m"] = np.where(
    independent_matched["date_et"]
    == independent_matched["date_et"].shift(-12),
    independent_matched["close"].shift(-12)
    / independent_matched["close"]
    - 1,
    np.nan
)

independent_matched = independent_matched.dropna(
    subset=["future_return_60m"]
)

print(
    f"Independent usable 60m signals: "
    f"{len(independent_matched)}"
)

print("\nINDEPENDENT MOMENTUM ACCURACY")

ind_correct = (
    (
        (independent_matched["signal"] == "BULLISH")
        & (independent_matched["future_return_60m"] > 0)
    )
    |
    (
        (independent_matched["signal"] == "BEARISH")
        & (independent_matched["future_return_60m"] < 0)
    )
)

ind_momentum_accuracy = (
    ind_correct.mean() * 100
    if len(independent_matched)
    else 0.0
)

print(f"Accuracy: {ind_momentum_accuracy:.1f}%")
print(f"Signals:  {len(independent_matched)}")
print(
    f"Edge:     "
    f"{ind_momentum_accuracy - 50:+.1f}%"
)

print("\nINDEPENDENT DIRECTIONAL RETURN")

ind_signed_return = np.where(
    independent_matched["signal"] == "BULLISH",
    independent_matched["future_return_60m"],
    -independent_matched["future_return_60m"]
)

ind_avg_return = (
    float(np.mean(ind_signed_return)) * 100
    if len(ind_signed_return)
    else 0.0
)

ind_median_return = (
    float(np.median(ind_signed_return)) * 100
    if len(ind_signed_return)
    else 0.0
)

print(
    f"Average directional return: "
    f"{ind_avg_return:+.4f}%"
)

print(
    f"Median directional return:  "
    f"{ind_median_return:+.4f}%"
)

print("\nFIRST VS INDEPENDENT MOMENTUM")

development_accuracy = float(
    best_momentum["accuracy"]
)

momentum_accuracy_change = (
    ind_momentum_accuracy
    - development_accuracy
)

print(
    f"Development accuracy: "
    f"{development_accuracy:.1f}%"
)

print(
    f"Independent accuracy: "
    f"{ind_momentum_accuracy:.1f}%"
)

print(
    f"Change: "
    f"{momentum_accuracy_change:+.1f}%"
)

print("\nV3.2 VALIDATION VERDICT")

momentum_independent_pass = (
    len(independent_matched) >= 30
    and ind_momentum_accuracy >= 55
    and ind_avg_return > 0
    and abs(momentum_accuracy_change) <= 10
)

if momentum_independent_pass:
    momentum_independent_verdict = (
        "PASSES INDEPENDENT MOMENTUM VALIDATION"
    )
else:
    momentum_independent_verdict = (
        "DOES NOT PASS INDEPENDENT MOMENTUM VALIDATION"
    )

print(
    f"Verdict: "
    f"{momentum_independent_verdict}"
)

print("RULES WERE NOT CHANGED FOR THIS TEST")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

momentum_validation = pd.DataFrame([{
    "development_accuracy": round(
        development_accuracy, 2
    ),
    "independent_signals": len(
        independent_matched
    ),
    "independent_accuracy": round(
        ind_momentum_accuracy, 2
    ),
    "accuracy_change": round(
        momentum_accuracy_change, 2
    ),
    "avg_directional_return": round(
        ind_avg_return, 5
    ),
    "median_directional_return": round(
        ind_median_return, 5
    ),
    "passed": momentum_independent_pass,
    "verdict": momentum_independent_verdict,
}])

momentum_validation.to_csv(
    "spy_sentinel_momentum_independent_validation.csv",
    index=False
)

print("Independent momentum validation saved")

print("\nV3.3 CORRECTED INDEPENDENT MOMENTUM TEST")

ind_corrected = independent.copy()

ind_corrected["future_return_60m_true"] = np.where(
    ind_corrected["date_et"]
    == ind_corrected["date_et"].shift(-12),
    ind_corrected["close"].shift(-12)
    / ind_corrected["close"]
    - 1,
    np.nan
)

print("True 12-candle forward returns calculated BEFORE filtering")

ind_corrected["momentum_15m"] = (
    ind_corrected["close"].pct_change(3)
)

ind_corrected["momentum_60m"] = (
    ind_corrected["close"].pct_change(12)
)

ind_corrected["momentum_15m_lag"] = (
    ind_corrected["momentum_15m"].shift(1)
)

ind_corrected["momentum_60m_lag"] = (
    ind_corrected["momentum_60m"].shift(1)
)

print("Lagged momentum recalculated")

ind_corrected["momentum_match"] = (
    (
        (ind_corrected["signal"] == "BULLISH")
        & (ind_corrected["momentum_15m_lag"] > 0)
        & (ind_corrected["momentum_60m_lag"] > 0)
    )
    |
    (
        (ind_corrected["signal"] == "BEARISH")
        & (ind_corrected["momentum_15m_lag"] < 0)
        & (ind_corrected["momentum_60m_lag"] < 0)
    )
)

ind_corrected["vwap_match"] = (
    (
        (ind_corrected["signal"] == "BULLISH")
        & (ind_corrected["close"] > ind_corrected["vwap"])
    )
    |
    (
        (ind_corrected["signal"] == "BEARISH")
        & (ind_corrected["close"] < ind_corrected["vwap"])
    )
)

corrected_match = ind_corrected[
    ind_corrected["momentum_match"]
    & ind_corrected["vwap_match"]
    & (ind_corrected["volume_ratio"] >= 1.0)
].dropna(
    subset=["future_return_60m_true"]
).copy()

print(f"Corrected independent signals: {len(corrected_match)}")

corrected_wins = (
    (
        (corrected_match["signal"] == "BULLISH")
        & (corrected_match["future_return_60m_true"] > 0)
    )
    |
    (
        (corrected_match["signal"] == "BEARISH")
        & (corrected_match["future_return_60m_true"] < 0)
    )
)

corrected_accuracy = (
    corrected_wins.mean() * 100
    if len(corrected_match)
    else 0.0
)

print("\nCORRECTED INDEPENDENT ACCURACY")
print(f"Signals:  {len(corrected_match)}")
print(f"Accuracy: {corrected_accuracy:.2f}%")
print(f"Edge:     {corrected_accuracy - 50:+.2f}%")

corrected_signed_return = np.where(
    corrected_match["signal"] == "BULLISH",
    corrected_match["future_return_60m_true"],
    -corrected_match["future_return_60m_true"]
)

corrected_avg_return = (
    float(np.mean(corrected_signed_return)) * 100
    if len(corrected_signed_return)
    else 0.0
)

corrected_median_return = (
    float(np.median(corrected_signed_return)) * 100
    if len(corrected_signed_return)
    else 0.0
)

print("\nCORRECTED RETURN QUALITY")
print(f"Average directional return: {corrected_avg_return:+.4f}%")
print(f"Median directional return:  {corrected_median_return:+.4f}%")

corrected_change = (
    corrected_accuracy
    - development_accuracy
)

print("\nDEVELOPMENT VS CORRECTED INDEPENDENT")
print(f"Development accuracy: {development_accuracy:.2f}%")
print(f"Independent accuracy: {corrected_accuracy:.2f}%")
print(f"Change:               {corrected_change:+.2f}%")

corrected_momentum_pass = (
    len(corrected_match) >= 30
    and corrected_accuracy >= 55
    and corrected_avg_return > 0
    and abs(corrected_change) <= 10
)

print("\nV3.3 CORRECTED VERDICT")

if corrected_momentum_pass:
    corrected_momentum_verdict = "PASSES CORRECTED INDEPENDENT VALIDATION"
else:
    corrected_momentum_verdict = "DOES NOT PASS CORRECTED INDEPENDENT VALIDATION"

print(f"Verdict: {corrected_momentum_verdict}")
print("NO RULES CHANGED FOR THIS CORRECTION")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

pd.DataFrame([{
    "development_accuracy": round(development_accuracy, 3),
    "independent_signals": len(corrected_match),
    "corrected_accuracy": round(corrected_accuracy, 3),
    "accuracy_change": round(corrected_change, 3),
    "avg_directional_return": round(corrected_avg_return, 5),
    "median_directional_return": round(corrected_median_return, 5),
    "passed": corrected_momentum_pass,
    "verdict": corrected_momentum_verdict,
}]).to_csv(
    "spy_sentinel_corrected_momentum_validation.csv",
    index=False
)

print("Corrected momentum validation saved")

print("\nV3.4 CONFLUENCE DEVELOPMENT TEST")

confluence = clean.copy()

confluence["mom15"] = confluence["close"].pct_change(3)
confluence["mom60"] = confluence["close"].pct_change(12)

confluence["mom15_lag"] = confluence["mom15"].shift(1)
confluence["mom60_lag"] = confluence["mom60"].shift(1)

confluence["ema9_slope3"] = (
    confluence["ema9"]
    - confluence["ema9"].shift(3)
).shift(1)

confluence["ema21_slope3"] = (
    confluence["ema21"]
    - confluence["ema21"].shift(3)
).shift(1)

print("Lagged momentum and EMA-slope features calculated")

confluence["vwap_match"] = (
    (
        (confluence["signal"] == "BULLISH")
        & (confluence["close"] > confluence["vwap"])
    )
    |
    (
        (confluence["signal"] == "BEARISH")
        & (confluence["close"] < confluence["vwap"])
    )
)

confluence["momentum_match"] = (
    (
        (confluence["signal"] == "BULLISH")
        & (confluence["mom15_lag"] > 0)
        & (confluence["mom60_lag"] > 0)
    )
    |
    (
        (confluence["signal"] == "BEARISH")
        & (confluence["mom15_lag"] < 0)
        & (confluence["mom60_lag"] < 0)
    )
)

confluence["slope_match"] = (
    (
        (confluence["signal"] == "BULLISH")
        & (confluence["ema9_slope3"] > 0)
        & (confluence["ema21_slope3"] > 0)
    )
    |
    (
        (confluence["signal"] == "BEARISH")
        & (confluence["ema9_slope3"] < 0)
        & (confluence["ema21_slope3"] < 0)
    )
)

print("Confluence flags calculated")

dev_base = confluence[
    confluence["signal"].isin(["BULLISH", "BEARISH"])
    & confluence["vwap_match"]
    & (confluence["volume_ratio"] >= 1.0)
].copy()

dev_momentum = dev_base[
    dev_base["momentum_match"]
].copy()

dev_slope = dev_base[
    dev_base["slope_match"]
].copy()

dev_full = dev_base[
    dev_base["momentum_match"]
    & dev_base["slope_match"]
].copy()

print(f"Base signals:       {len(dev_base)}")
print(f"+ Momentum:         {len(dev_momentum)}")
print(f"+ EMA slope:        {len(dev_slope)}")
print(f"Full confluence:    {len(dev_full)}")

def evaluate_confluence(frame, name):

    sample = frame.dropna(
        subset=["future_return_60m"]
    ).copy()

    if sample.empty:
        return {
            "strategy": name,
            "signals": 0,
            "accuracy": 0.0,
            "avg_return": 0.0,
        }

    correct = (
        (
            (sample["signal"] == "BULLISH")
            & (sample["future_return_60m"] > 0)
        )
        |
        (
            (sample["signal"] == "BEARISH")
            & (sample["future_return_60m"] < 0)
        )
    )

    signed_returns = np.where(
        sample["signal"] == "BULLISH",
        sample["future_return_60m"],
        -sample["future_return_60m"]
    )

    return {
        "strategy": name,
        "signals": len(sample),
        "accuracy": correct.mean() * 100,
        "avg_return": float(np.mean(signed_returns)) * 100,
    }

development_results = []

development_results.append(
    evaluate_confluence(dev_base, "BASE")
)

development_results.append(
    evaluate_confluence(dev_momentum, "MOMENTUM")
)

development_results.append(
    evaluate_confluence(dev_slope, "EMA_SLOPE")
)

development_results.append(
    evaluate_confluence(dev_full, "FULL_CONFLUENCE")
)

development_df = pd.DataFrame(development_results)

print("\nDEVELOPMENT COMPARISON")

for _, row in development_df.iterrows():
    print(
        f"{row['strategy']}: "
        f"{row['accuracy']:.1f}% | "
        f"{int(row['signals'])} signals | "
        f"avg directional return "
        f"{row['avg_return']:+.4f}%"
    )

print("\nMINIMUM SAMPLE GATE")

usable_dev = development_df[
    (development_df["signals"] >= 50)
    & (development_df["avg_return"] > 0)
].copy()

if not usable_dev.empty:

    best_dev = usable_dev.sort_values(
        ["accuracy", "avg_return"],
        ascending=False
    ).iloc[0]

    candidate_strategy = best_dev["strategy"]

    print(f"Best candidate: {candidate_strategy}")
    print(f"Accuracy:       {best_dev['accuracy']:.1f}%")
    print(f"Signals:        {int(best_dev['signals'])}")
    print(
        f"Avg return:     "
        f"{best_dev['avg_return']:+.4f}%"
    )

else:

    best_dev = None
    candidate_strategy = "NONE"

    print("No candidate passed the minimum sample gate.")

print("\nV3.4 DEVELOPMENT VERDICT")

if (
    best_dev is not None
    and best_dev["accuracy"] >= 55
    and best_dev["signals"] >= 50
    and best_dev["avg_return"] > 0
):
    dev_candidate_pass = True
    dev_verdict = "CANDIDATE READY FOR INDEPENDENT TEST"
else:
    dev_candidate_pass = False
    dev_verdict = "NO DEVELOPMENT CANDIDATE"

print(f"Candidate: {candidate_strategy}")
print(f"Verdict:   {dev_verdict}")

print("IMPORTANT: DEVELOPMENT DATA ONLY")
print("INDEPENDENT DATA WAS NOT USED TO PICK THIS CANDIDATE")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

development_df.to_csv(
    "spy_sentinel_confluence_development.csv",
    index=False
)

pd.DataFrame([{
    "candidate_strategy": candidate_strategy,
    "candidate_pass": dev_candidate_pass,
    "verdict": dev_verdict,
}]).to_csv(
    "spy_sentinel_confluence_candidate.csv",
    index=False
)

print("Confluence development research saved")

print("\nV3.5 INDEPENDENT CONFLUENCE TEST")

ind_conf = independent.copy()

ind_conf["future_return_60m_true"] = np.where(
    ind_conf["date_et"]
    == ind_conf["date_et"].shift(-12),
    ind_conf["close"].shift(-12)
    / ind_conf["close"]
    - 1,
    np.nan
)

print("True 60-minute returns calculated before filtering")

ind_conf["mom15"] = (
    ind_conf["close"].pct_change(3)
)

ind_conf["mom60"] = (
    ind_conf["close"].pct_change(12)
)

ind_conf["mom15_lag"] = (
    ind_conf["mom15"].shift(1)
)

ind_conf["mom60_lag"] = (
    ind_conf["mom60"].shift(1)
)

ind_conf["ema9_slope3"] = (
    ind_conf["ema9"]
    - ind_conf["ema9"].shift(3)
).shift(1)

ind_conf["ema21_slope3"] = (
    ind_conf["ema21"]
    - ind_conf["ema21"].shift(3)
).shift(1)

print("Independent confluence features calculated")

ind_conf["vwap_match"] = (
    (
        (ind_conf["signal"] == "BULLISH")
        & (ind_conf["close"] > ind_conf["vwap"])
    )
    |
    (
        (ind_conf["signal"] == "BEARISH")
        & (ind_conf["close"] < ind_conf["vwap"])
    )
)

ind_conf["momentum_match"] = (
    (
        (ind_conf["signal"] == "BULLISH")
        & (ind_conf["mom15_lag"] > 0)
        & (ind_conf["mom60_lag"] > 0)
    )
    |
    (
        (ind_conf["signal"] == "BEARISH")
        & (ind_conf["mom15_lag"] < 0)
        & (ind_conf["mom60_lag"] < 0)
    )
)

ind_conf["slope_match"] = (
    (
        (ind_conf["signal"] == "BULLISH")
        & (ind_conf["ema9_slope3"] > 0)
        & (ind_conf["ema21_slope3"] > 0)
    )
    |
    (
        (ind_conf["signal"] == "BEARISH")
        & (ind_conf["ema9_slope3"] < 0)
        & (ind_conf["ema21_slope3"] < 0)
    )
)

print("Independent match flags calculated")

ind_base = ind_conf[
    ind_conf["signal"].isin(["BULLISH", "BEARISH"])
    & ind_conf["vwap_match"]
    & (ind_conf["volume_ratio"] >= 1.0)
].copy()

if candidate_strategy == "MOMENTUM":

    ind_candidate = ind_base[
        ind_base["momentum_match"]
    ].copy()

elif candidate_strategy == "EMA_SLOPE":

    ind_candidate = ind_base[
        ind_base["slope_match"]
    ].copy()

elif candidate_strategy == "FULL_CONFLUENCE":

    ind_candidate = ind_base[
        ind_base["momentum_match"]
        & ind_base["slope_match"]
    ].copy()

else:

    ind_candidate = ind_base.copy()

ind_candidate = ind_candidate.dropna(
    subset=["future_return_60m_true"]
)

print(f"Candidate tested: {candidate_strategy}")
print(f"Independent signals: {len(ind_candidate)}")

print("\nINDEPENDENT CONFLUENCE ACCURACY")

ind_conf_correct = (
    (
        (ind_candidate["signal"] == "BULLISH")
        & (ind_candidate["future_return_60m_true"] > 0)
    )
    |
    (
        (ind_candidate["signal"] == "BEARISH")
        & (ind_candidate["future_return_60m_true"] < 0)
    )
)

ind_conf_accuracy = (
    ind_conf_correct.mean() * 100
    if len(ind_candidate)
    else 0.0
)

print(f"Accuracy: {ind_conf_accuracy:.2f}%")
print(f"Signals:  {len(ind_candidate)}")
print(f"Edge:     {ind_conf_accuracy - 50:+.2f}%")

ind_conf_signed = np.where(
    ind_candidate["signal"] == "BULLISH",
    ind_candidate["future_return_60m_true"],
    -ind_candidate["future_return_60m_true"]
)

ind_conf_avg_return = (
    float(np.mean(ind_conf_signed)) * 100
    if len(ind_conf_signed)
    else 0.0
)

ind_conf_median_return = (
    float(np.median(ind_conf_signed)) * 100
    if len(ind_conf_signed)
    else 0.0
)

print("\nINDEPENDENT RETURN QUALITY")
print(
    f"Average directional return: "
    f"{ind_conf_avg_return:+.4f}%"
)
print(
    f"Median directional return:  "
    f"{ind_conf_median_return:+.4f}%"
)

development_candidate_accuracy = (
    float(best_dev["accuracy"])
    if best_dev is not None
    else 0.0
)

confluence_change = (
    ind_conf_accuracy
    - development_candidate_accuracy
)

confluence_independent_pass = (
    len(ind_candidate) >= 30
    and ind_conf_accuracy >= 55
    and ind_conf_avg_return > 0
    and abs(confluence_change) <= 10
)

print("\nV3.5 INDEPENDENT VERDICT")
print(
    f"Development accuracy: "
    f"{development_candidate_accuracy:.2f}%"
)
print(
    f"Independent accuracy: "
    f"{ind_conf_accuracy:.2f}%"
)
print(f"Change: {confluence_change:+.2f}%")

if confluence_independent_pass:
    confluence_verdict = (
        "PASSES INDEPENDENT CONFLUENCE VALIDATION"
    )
else:
    confluence_verdict = (
        "DOES NOT PASS INDEPENDENT CONFLUENCE VALIDATION"
    )

print(f"Verdict: {confluence_verdict}")
print("RULES WERE NOT CHANGED FOR THIS TEST")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

pd.DataFrame([{
    "candidate": candidate_strategy,
    "development_accuracy": round(
        development_candidate_accuracy, 3
    ),
    "independent_signals": len(ind_candidate),
    "independent_accuracy": round(
        ind_conf_accuracy, 3
    ),
    "accuracy_change": round(
        confluence_change, 3
    ),
    "avg_directional_return": round(
        ind_conf_avg_return, 5
    ),
    "median_directional_return": round(
        ind_conf_median_return, 5
    ),
    "passed": confluence_independent_pass,
    "verdict": confluence_verdict,
}]).to_csv(
    "spy_sentinel_confluence_independent.csv",
    index=False
)

print("Independent confluence validation saved")

print("\nV3.6 TREND-REGIME DEVELOPMENT")

trend_dev = clean.copy()

trend_dev["ema50"] = (
    trend_dev["close"]
    .ewm(span=50, adjust=False)
    .mean()
)

trend_dev["ema50_slope5"] = (
    trend_dev["ema50"]
    - trend_dev["ema50"].shift(5)
).shift(1)

print("EMA50 regime features calculated")

trend_dev["long_regime"] = (
    (trend_dev["close"] > trend_dev["ema50"])
    & (trend_dev["ema50_slope5"] > 0)
)

trend_dev["short_regime"] = (
    (trend_dev["close"] < trend_dev["ema50"])
    & (trend_dev["ema50_slope5"] < 0)
)

trend_dev["regime_match"] = (
    (
        (trend_dev["signal"] == "BULLISH")
        & trend_dev["long_regime"]
    )
    |
    (
        (trend_dev["signal"] == "BEARISH")
        & trend_dev["short_regime"]
    )
)

print("Trend-regime flags calculated")

trend_candidate = trend_dev[
    trend_dev["signal"].isin(["BULLISH", "BEARISH"])
    & trend_dev["regime_match"]
    & (
        (
            (trend_dev["signal"] == "BULLISH")
            & (trend_dev["close"] > trend_dev["vwap"])
        )
        |
        (
            (trend_dev["signal"] == "BEARISH")
            & (trend_dev["close"] < trend_dev["vwap"])
        )
    )
].dropna(
    subset=["future_return_60m"]
).copy()

print(f"Trend-regime signals: {len(trend_candidate)}")

trend_correct = (
    (
        (trend_candidate["signal"] == "BULLISH")
        & (trend_candidate["future_return_60m"] > 0)
    )
    |
    (
        (trend_candidate["signal"] == "BEARISH")
        & (trend_candidate["future_return_60m"] < 0)
    )
)

trend_accuracy = (
    trend_correct.mean() * 100
    if len(trend_candidate)
    else 0.0
)

trend_signed = np.where(
    trend_candidate["signal"] == "BULLISH",
    trend_candidate["future_return_60m"],
    -trend_candidate["future_return_60m"]
)

trend_avg_return = (
    float(np.mean(trend_signed)) * 100
    if len(trend_signed)
    else 0.0
)

print("\nTREND-REGIME DEVELOPMENT RESULTS")
print(f"Accuracy:    {trend_accuracy:.2f}%")
print(f"Signals:     {len(trend_candidate)}")
print(f"Avg return:  {trend_avg_return:+.4f}%")

print("\nDIRECTION SPLIT")

for direction in ["BULLISH", "BEARISH"]:

    d = trend_candidate[
        trend_candidate["signal"] == direction
    ].copy()

    if direction == "BULLISH":
        d_correct = d["future_return_60m"] > 0
    else:
        d_correct = d["future_return_60m"] < 0

    d_accuracy = (
        d_correct.mean() * 100
        if len(d)
        else 0.0
    )

    print(
        f"{direction}: "
        f"{d_accuracy:.1f}% | "
        f"{len(d)} signals"
    )

print("\nV3.6 DEVELOPMENT GATE")

trend_dev_pass = (
    len(trend_candidate) >= 50
    and trend_accuracy >= 55
    and trend_avg_return > 0
)

if trend_dev_pass:
    trend_dev_verdict = "READY FOR INDEPENDENT TEST"
else:
    trend_dev_verdict = "NOT STRONG ENOUGH"

print(f"Verdict: {trend_dev_verdict}")
print("DEVELOPMENT DATA ONLY")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

pd.DataFrame([{
    "signals": len(trend_candidate),
    "accuracy": round(trend_accuracy, 3),
    "avg_directional_return": round(trend_avg_return, 5),
    "passed": trend_dev_pass,
    "verdict": trend_dev_verdict,
}]).to_csv(
    "spy_sentinel_trend_regime_development.csv",
    index=False
)

print("Trend-regime development saved")

print("\nV3.7 INDEPENDENT TREND-REGIME TEST")

ind_trend = independent.copy()

ind_trend["future_return_60m_true"] = np.where(
    ind_trend["date_et"] == ind_trend["date_et"].shift(-12),
    ind_trend["close"].shift(-12) / ind_trend["close"] - 1,
    np.nan
)

print("True 60-minute returns calculated before filtering")

ind_trend["ema50"] = (
    ind_trend["close"]
    .ewm(span=50, adjust=False)
    .mean()
)

ind_trend["ema50_slope5"] = (
    ind_trend["ema50"]
    - ind_trend["ema50"].shift(5)
).shift(1)

print("Independent EMA50 regime features calculated")

ind_trend["long_regime"] = (
    (ind_trend["close"] > ind_trend["ema50"])
    & (ind_trend["ema50_slope5"] > 0)
)

ind_trend["short_regime"] = (
    (ind_trend["close"] < ind_trend["ema50"])
    & (ind_trend["ema50_slope5"] < 0)
)

ind_trend["regime_match"] = (
    (
        (ind_trend["signal"] == "BULLISH")
        & ind_trend["long_regime"]
    )
    |
    (
        (ind_trend["signal"] == "BEARISH")
        & ind_trend["short_regime"]
    )
)

print("Independent regime flags calculated")

ind_trend_candidate = ind_trend[
    ind_trend["signal"].isin(["BULLISH", "BEARISH"])
    & ind_trend["regime_match"]
    & (
        (
            (ind_trend["signal"] == "BULLISH")
            & (ind_trend["close"] > ind_trend["vwap"])
        )
        |
        (
            (ind_trend["signal"] == "BEARISH")
            & (ind_trend["close"] < ind_trend["vwap"])
        )
    )
].dropna(
    subset=["future_return_60m_true"]
).copy()

print(
    f"Independent trend-regime signals: "
    f"{len(ind_trend_candidate)}"
)

ind_trend_correct = (
    (
        (ind_trend_candidate["signal"] == "BULLISH")
        & (ind_trend_candidate["future_return_60m_true"] > 0)
    )
    |
    (
        (ind_trend_candidate["signal"] == "BEARISH")
        & (ind_trend_candidate["future_return_60m_true"] < 0)
    )
)

ind_trend_accuracy = (
    ind_trend_correct.mean() * 100
    if len(ind_trend_candidate)
    else 0.0
)

print("\nINDEPENDENT TREND-REGIME RESULTS")
print(f"Accuracy: {ind_trend_accuracy:.2f}%")
print(f"Signals:  {len(ind_trend_candidate)}")
print(f"Edge:     {ind_trend_accuracy - 50:+.2f}%")

ind_trend_signed = np.where(
    ind_trend_candidate["signal"] == "BULLISH",
    ind_trend_candidate["future_return_60m_true"],
    -ind_trend_candidate["future_return_60m_true"]
)

ind_trend_avg_return = (
    float(np.mean(ind_trend_signed)) * 100
    if len(ind_trend_signed)
    else 0.0
)

ind_trend_median_return = (
    float(np.median(ind_trend_signed)) * 100
    if len(ind_trend_signed)
    else 0.0
)

print("\nINDEPENDENT RETURN QUALITY")
print(
    f"Average directional return: "
    f"{ind_trend_avg_return:+.4f}%"
)
print(
    f"Median directional return:  "
    f"{ind_trend_median_return:+.4f}%"
)

trend_accuracy_change = (
    ind_trend_accuracy - trend_accuracy
)

trend_independent_pass = (
    len(ind_trend_candidate) >= 100
    and ind_trend_accuracy >= 55
    and ind_trend_avg_return > 0
    and abs(trend_accuracy_change) <= 10
)

print("\nV3.7 INDEPENDENT VERDICT")

print(f"Development accuracy: {trend_accuracy:.2f}%")
print(f"Independent accuracy: {ind_trend_accuracy:.2f}%")
print(f"Change:               {trend_accuracy_change:+.2f}%")

if trend_independent_pass:
    trend_independent_verdict = (
        "PASSES INDEPENDENT TREND-REGIME VALIDATION"
    )
else:
    trend_independent_verdict = (
        "DOES NOT PASS INDEPENDENT TREND-REGIME VALIDATION"
    )

print(f"Verdict: {trend_independent_verdict}")
print("RULES WERE NOT CHANGED FOR THIS TEST")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

pd.DataFrame([{
    "development_signals": len(trend_candidate),
    "development_accuracy": round(trend_accuracy, 3),
    "independent_signals": len(ind_trend_candidate),
    "independent_accuracy": round(ind_trend_accuracy, 3),
    "accuracy_change": round(trend_accuracy_change, 3),
    "avg_directional_return": round(ind_trend_avg_return, 5),
    "median_directional_return": round(ind_trend_median_return, 5),
    "passed": trend_independent_pass,
    "verdict": trend_independent_verdict,
}]).to_csv(
    "spy_sentinel_trend_regime_independent.csv",
    index=False
)

print("Independent trend-regime validation saved")

print("\nV3.8 BULLISH-ONLY DEVELOPMENT")

bull_dev = trend_candidate[
    trend_candidate["signal"] == "BULLISH"
].dropna(
    subset=["future_return_60m"]
).copy()

bull_dev_correct = (
    bull_dev["future_return_60m"] > 0
)

bull_dev_accuracy = (
    bull_dev_correct.mean() * 100
    if len(bull_dev)
    else 0.0
)

bull_dev_avg_return = (
    bull_dev["future_return_60m"].mean() * 100
    if len(bull_dev)
    else 0.0
)

print(f"Signals:        {len(bull_dev)}")
print(f"Accuracy:       {bull_dev_accuracy:.2f}%")
print(f"Average return: {bull_dev_avg_return:+.4f}%")

bull_dev_candidate = (
    len(bull_dev) >= 100
    and bull_dev_accuracy >= 55
    and bull_dev_avg_return > 0
)

print("\nBULLISH DEVELOPMENT GATE")
print(f"Candidate: {bull_dev_candidate}")

if bull_dev_candidate:
    print("Development verdict: TEST BULLISH-ONLY INDEPENDENTLY")
else:
    print("Development verdict: BULLISH-ONLY NOT STRONG ENOUGH")

print("Direction was selected from DEVELOPMENT data only")

print("\nV3.8 BULLISH-ONLY INDEPENDENT TEST")

bull_ind = ind_trend_candidate[
    ind_trend_candidate["signal"] == "BULLISH"
].dropna(
    subset=["future_return_60m_true"]
).copy()

bull_ind_correct = (
    bull_ind["future_return_60m_true"] > 0
)

bull_ind_accuracy = (
    bull_ind_correct.mean() * 100
    if len(bull_ind)
    else 0.0
)

bull_ind_avg_return = (
    bull_ind["future_return_60m_true"].mean() * 100
    if len(bull_ind)
    else 0.0
)

bull_ind_median_return = (
    bull_ind["future_return_60m_true"].median() * 100
    if len(bull_ind)
    else 0.0
)

print(f"Signals:        {len(bull_ind)}")
print(f"Accuracy:       {bull_ind_accuracy:.2f}%")
print(f"Average return: {bull_ind_avg_return:+.4f}%")
print(f"Median return:  {bull_ind_median_return:+.4f}%")

bull_accuracy_change = (
    bull_ind_accuracy
    - bull_dev_accuracy
)

print("\nDEVELOPMENT VS INDEPENDENT BULLISH")

print(f"Development: {bull_dev_accuracy:.2f}%")
print(f"Independent: {bull_ind_accuracy:.2f}%")
print(f"Change:      {bull_accuracy_change:+.2f}%")

print("\nBULLISH WILSON INTERVAL")

n_bull = len(bull_ind)
wins_bull = int(bull_ind_correct.sum())

if n_bull > 0:

    p_bull = wins_bull / n_bull
    z = 1.96

    denom = 1 + z**2 / n_bull

    center = (
        p_bull + z**2 / (2 * n_bull)
    ) / denom

    margin = (
        z * np.sqrt(
            p_bull * (1 - p_bull) / n_bull
            + z**2 / (4 * n_bull**2)
        ) / denom
    )

    bull_ci_low = center - margin
    bull_ci_high = center + margin

else:

    bull_ci_low = 0
    bull_ci_high = 0

print(f"95% CI low:  {bull_ci_low * 100:.2f}%")
print(f"95% CI high: {bull_ci_high * 100:.2f}%")
print(f"CI above 50%: {bull_ci_low > 0.50}")

print("\nBULLISH INDEPENDENT VALIDATION GATE")

bull_independent_pass = (
    bull_dev_candidate
    and len(bull_ind) >= 100
    and bull_ind_accuracy >= 55
    and bull_ind_avg_return > 0
    and abs(bull_accuracy_change) <= 10
)

if bull_independent_pass:
    bull_verdict = "PASSES BULLISH-ONLY INDEPENDENT VALIDATION"
else:
    bull_verdict = "DOES NOT PASS BULLISH-ONLY INDEPENDENT VALIDATION"

print(f"Verdict: {bull_verdict}")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

pd.DataFrame([{
    "development_signals": len(bull_dev),
    "development_accuracy": round(bull_dev_accuracy, 3),
    "development_avg_return": round(bull_dev_avg_return, 5),
    "independent_signals": len(bull_ind),
    "independent_accuracy": round(bull_ind_accuracy, 3),
    "independent_avg_return": round(bull_ind_avg_return, 5),
    "independent_median_return": round(bull_ind_median_return, 5),
    "accuracy_change": round(bull_accuracy_change, 3),
    "ci_low": round(bull_ci_low * 100, 3),
    "ci_high": round(bull_ci_high * 100, 3),
    "passed": bull_independent_pass,
    "verdict": bull_verdict,
}]).to_csv(
    "spy_sentinel_bullish_only_validation.csv",
    index=False
)

print("Bullish-only validation saved")

print("\nV3.9 BREAKOUT DEVELOPMENT")

breakout = clean.copy()

breakout["high20_prev"] = (
    breakout["high"]
    .rolling(20)
    .max()
    .shift(1)
)

breakout["low20_prev"] = (
    breakout["low"]
    .rolling(20)
    .min()
    .shift(1)
)

breakout["range20"] = (
    breakout["high20_prev"]
    - breakout["low20_prev"]
)

print("20-bar breakout levels calculated")

breakout["bull_breakout"] = (
    (breakout["close"] > breakout["high20_prev"])
    & (breakout["volume_ratio"] >= 1.2)
    & (breakout["close"] > breakout["vwap"])
)

breakout["bear_breakout"] = (
    (breakout["close"] < breakout["low20_prev"])
    & (breakout["volume_ratio"] >= 1.2)
    & (breakout["close"] < breakout["vwap"])
)

breakout["breakout_signal"] = np.where(
    breakout["bull_breakout"],
    "BULLISH",
    np.where(
        breakout["bear_breakout"],
        "BEARISH",
        "NO TRADE"
    )
)

print("Breakout signals generated")

breakout_signals = breakout[
    breakout["breakout_signal"].isin(
        ["BULLISH", "BEARISH"]
    )
].dropna(
    subset=["future_return_60m"]
).copy()

print(f"Breakout signals: {len(breakout_signals)}")

breakout_correct = (
    (
        (breakout_signals["breakout_signal"] == "BULLISH")
        & (breakout_signals["future_return_60m"] > 0)
    )
    |
    (
        (breakout_signals["breakout_signal"] == "BEARISH")
        & (breakout_signals["future_return_60m"] < 0)
    )
)

breakout_accuracy = (
    breakout_correct.mean() * 100
    if len(breakout_signals)
    else 0.0
)

print("\nBREAKOUT ACCURACY")
print(f"Accuracy: {breakout_accuracy:.2f}%")
print(f"Signals:  {len(breakout_signals)}")
print(f"Edge:     {breakout_accuracy - 50:+.2f}%")

breakout_signed = np.where(
    breakout_signals["breakout_signal"] == "BULLISH",
    breakout_signals["future_return_60m"],
    -breakout_signals["future_return_60m"]
)

breakout_avg_return = (
    float(np.mean(breakout_signed)) * 100
    if len(breakout_signed)
    else 0.0
)

breakout_median_return = (
    float(np.median(breakout_signed)) * 100
    if len(breakout_signed)
    else 0.0
)

print("\nBREAKOUT RETURN QUALITY")
print(f"Average directional return: {breakout_avg_return:+.4f}%")
print(f"Median directional return:  {breakout_median_return:+.4f}%")

print("\nBREAKOUT DIRECTION SPLIT")

for direction in ["BULLISH", "BEARISH"]:

    d = breakout_signals[
        breakout_signals["breakout_signal"] == direction
    ].copy()

    if direction == "BULLISH":
        correct = d["future_return_60m"] > 0
    else:
        correct = d["future_return_60m"] < 0

    acc = (
        correct.mean() * 100
        if len(d)
        else 0.0
    )

    print(
        f"{direction}: "
        f"{acc:.1f}% | "
        f"{len(d)} signals"
    )

print("\nV3.9 DEVELOPMENT GATE")

breakout_candidate = (
    len(breakout_signals) >= 50
    and breakout_accuracy >= 55
    and breakout_avg_return > 0
)

if breakout_candidate:
    breakout_verdict = "READY FOR INDEPENDENT TEST"
else:
    breakout_verdict = "NOT STRONG ENOUGH"

print(f"Verdict: {breakout_verdict}")
print("DEVELOPMENT DATA ONLY")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

pd.DataFrame([{
    "signals": len(breakout_signals),
    "accuracy": round(breakout_accuracy, 3),
    "avg_directional_return": round(breakout_avg_return, 5),
    "median_directional_return": round(breakout_median_return, 5),
    "candidate": breakout_candidate,
    "verdict": breakout_verdict,
}]).to_csv(
    "spy_sentinel_breakout_development.csv",
    index=False
)

print("Breakout development saved")

print("\nV4.0 MEAN-REVERSION DEVELOPMENT")

mr = clean.copy()

mr["bb_mid"] = (
    mr["close"]
    .rolling(20)
    .mean()
)

mr["bb_std"] = (
    mr["close"]
    .rolling(20)
    .std()
)

mr["bb_upper"] = (
    mr["bb_mid"]
    + 2 * mr["bb_std"]
)

mr["bb_lower"] = (
    mr["bb_mid"]
    - 2 * mr["bb_std"]
)

print("Bollinger-style reversion bands calculated")

mr["bull_reversion"] = (
    (mr["close"] < mr["bb_lower"])
    & (mr["rsi14"] <= 40)
)

mr["bear_reversion"] = (
    (mr["close"] > mr["bb_upper"])
    & (mr["rsi14"] >= 60)
)

mr["mr_signal"] = np.where(
    mr["bull_reversion"],
    "BULLISH",
    np.where(
        mr["bear_reversion"],
        "BEARISH",
        "NO TRADE"
    )
)

print("Mean-reversion signals generated")

mr_signals = mr[
    mr["mr_signal"].isin(
        ["BULLISH", "BEARISH"]
    )
].copy()

print(f"Mean-reversion signals: {len(mr_signals)}")

print("\nMEAN-REVERSION 30M TEST")

mr30 = mr_signals.dropna(
    subset=["future_return_30m"]
).copy()

mr30_correct = (
    (
        (mr30["mr_signal"] == "BULLISH")
        & (mr30["future_return_30m"] > 0)
    )
    |
    (
        (mr30["mr_signal"] == "BEARISH")
        & (mr30["future_return_30m"] < 0)
    )
)

mr30_accuracy = (
    mr30_correct.mean() * 100
    if len(mr30)
    else 0.0
)

print(f"Accuracy: {mr30_accuracy:.2f}%")
print(f"Signals:  {len(mr30)}")
print(f"Edge:     {mr30_accuracy - 50:+.2f}%")

print("\nMEAN-REVERSION 60M TEST")

mr60 = mr_signals.dropna(
    subset=["future_return_60m"]
).copy()

mr60_correct = (
    (
        (mr60["mr_signal"] == "BULLISH")
        & (mr60["future_return_60m"] > 0)
    )
    |
    (
        (mr60["mr_signal"] == "BEARISH")
        & (mr60["future_return_60m"] < 0)
    )
)

mr60_accuracy = (
    mr60_correct.mean() * 100
    if len(mr60)
    else 0.0
)

print(f"Accuracy: {mr60_accuracy:.2f}%")
print(f"Signals:  {len(mr60)}")
print(f"Edge:     {mr60_accuracy - 50:+.2f}%")

mr30_signed = np.where(
    mr30["mr_signal"] == "BULLISH",
    mr30["future_return_30m"],
    -mr30["future_return_30m"]
)

mr30_avg_return = (
    float(np.mean(mr30_signed)) * 100
    if len(mr30_signed)
    else 0.0
)

mr60_signed = np.where(
    mr60["mr_signal"] == "BULLISH",
    mr60["future_return_60m"],
    -mr60["future_return_60m"]
)

mr60_avg_return = (
    float(np.mean(mr60_signed)) * 100
    if len(mr60_signed)
    else 0.0
)

print("\nMEAN-REVERSION RETURN QUALITY")
print(f"30m average directional return: {mr30_avg_return:+.4f}%")
print(f"60m average directional return: {mr60_avg_return:+.4f}%")

print("\nMEAN-REVERSION DIRECTION SPLIT")

for direction in ["BULLISH", "BEARISH"]:

    d = mr30[
        mr30["mr_signal"] == direction
    ].copy()

    if direction == "BULLISH":
        correct = d["future_return_30m"] > 0
    else:
        correct = d["future_return_30m"] < 0

    accuracy = (
        correct.mean() * 100
        if len(d)
        else 0.0
    )

    print(
        f"{direction}: "
        f"{accuracy:.1f}% | "
        f"{len(d)} signals"
    )

print("\nV4.0 DEVELOPMENT GATE")

if (
    mr30_accuracy >= mr60_accuracy
):
    mr_best_horizon = "30m"
    mr_best_accuracy = mr30_accuracy
    mr_best_signals = len(mr30)
    mr_best_return = mr30_avg_return
else:
    mr_best_horizon = "60m"
    mr_best_accuracy = mr60_accuracy
    mr_best_signals = len(mr60)
    mr_best_return = mr60_avg_return

mr_candidate = (
    mr_best_signals >= 50
    and mr_best_accuracy >= 55
    and mr_best_return > 0
)

print(f"Best horizon: {mr_best_horizon}")
print(f"Accuracy:     {mr_best_accuracy:.2f}%")
print(f"Signals:      {mr_best_signals}")
print(f"Avg return:   {mr_best_return:+.4f}%")

if mr_candidate:
    mr_verdict = "READY FOR INDEPENDENT TEST"
else:
    mr_verdict = "NOT STRONG ENOUGH"

print(f"Verdict: {mr_verdict}")
print("DEVELOPMENT DATA ONLY")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

pd.DataFrame([{
    "best_horizon": mr_best_horizon,
    "accuracy": round(mr_best_accuracy, 3),
    "signals": mr_best_signals,
    "avg_directional_return": round(mr_best_return, 5),
    "candidate": mr_candidate,
    "verdict": mr_verdict,
}]).to_csv(
    "spy_sentinel_mean_reversion_development.csv",
    index=False
)

print("Mean-reversion development saved")

print("\nV4.1 INDEPENDENT MEAN-REVERSION TEST")

ind_mr = independent.copy()

ind_mr["future_return_60m_true"] = np.where(
    ind_mr["date_et"] == ind_mr["date_et"].shift(-12),
    ind_mr["close"].shift(-12) / ind_mr["close"] - 1,
    np.nan
)

print("True independent 60-minute returns calculated before filtering")

ind_mr["bb_mid"] = (
    ind_mr["close"]
    .rolling(20)
    .mean()
)

ind_mr["bb_std"] = (
    ind_mr["close"]
    .rolling(20)
    .std()
)

ind_mr["bb_upper"] = (
    ind_mr["bb_mid"]
    + 2 * ind_mr["bb_std"]
)

ind_mr["bb_lower"] = (
    ind_mr["bb_mid"]
    - 2 * ind_mr["bb_std"]
)

print("Independent Bollinger-style bands calculated")

ind_mr["bull_reversion"] = (
    (ind_mr["close"] < ind_mr["bb_lower"])
    & (ind_mr["rsi14"] <= 40)
)

ind_mr["bear_reversion"] = (
    (ind_mr["close"] > ind_mr["bb_upper"])
    & (ind_mr["rsi14"] >= 60)
)

ind_mr["mr_signal"] = np.where(
    ind_mr["bull_reversion"],
    "BULLISH",
    np.where(
        ind_mr["bear_reversion"],
        "BEARISH",
        "NO TRADE"
    )
)

ind_mr_signals = ind_mr[
    ind_mr["mr_signal"].isin(
        ["BULLISH", "BEARISH"]
    )
].dropna(
    subset=["future_return_60m_true"]
).copy()

print(
    f"Independent mean-reversion signals: "
    f"{len(ind_mr_signals)}"
)

ind_mr_correct = (
    (
        (ind_mr_signals["mr_signal"] == "BULLISH")
        & (ind_mr_signals["future_return_60m_true"] > 0)
    )
    |
    (
        (ind_mr_signals["mr_signal"] == "BEARISH")
        & (ind_mr_signals["future_return_60m_true"] < 0)
    )
)

ind_mr_accuracy = (
    ind_mr_correct.mean() * 100
    if len(ind_mr_signals)
    else 0.0
)

print("\nINDEPENDENT MEAN-REVERSION ACCURACY")
print(f"Accuracy: {ind_mr_accuracy:.2f}%")
print(f"Signals:  {len(ind_mr_signals)}")
print(f"Edge:     {ind_mr_accuracy - 50:+.2f}%")

ind_mr_signed = np.where(
    ind_mr_signals["mr_signal"] == "BULLISH",
    ind_mr_signals["future_return_60m_true"],
    -ind_mr_signals["future_return_60m_true"]
)

ind_mr_avg_return = (
    float(np.mean(ind_mr_signed)) * 100
    if len(ind_mr_signed)
    else 0.0
)

ind_mr_median_return = (
    float(np.median(ind_mr_signed)) * 100
    if len(ind_mr_signed)
    else 0.0
)

print("\nINDEPENDENT RETURN QUALITY")
print(
    f"Average directional return: "
    f"{ind_mr_avg_return:+.4f}%"
)
print(
    f"Median directional return:  "
    f"{ind_mr_median_return:+.4f}%"
)

print("\nINDEPENDENT DIRECTION SPLIT")

for direction in ["BULLISH", "BEARISH"]:

    d = ind_mr_signals[
        ind_mr_signals["mr_signal"] == direction
    ].copy()

    if direction == "BULLISH":
        correct = d["future_return_60m_true"] > 0
    else:
        correct = d["future_return_60m_true"] < 0

    acc = (
        correct.mean() * 100
        if len(d)
        else 0.0
    )

    print(
        f"{direction}: "
        f"{acc:.1f}% | "
        f"{len(d)} signals"
    )

mr_accuracy_change = (
    ind_mr_accuracy - mr_best_accuracy
)

mr_independent_pass = (
    len(ind_mr_signals) >= 100
    and ind_mr_accuracy >= 55
    and ind_mr_avg_return > 0
    and abs(mr_accuracy_change) <= 10
)

print("\nV4.1 INDEPENDENT VERDICT")

print(f"Development accuracy: {mr_best_accuracy:.2f}%")
print(f"Independent accuracy: {ind_mr_accuracy:.2f}%")
print(f"Change:               {mr_accuracy_change:+.2f}%")

if mr_independent_pass:
    mr_ind_verdict = (
        "PASSES INDEPENDENT MEAN-REVERSION VALIDATION"
    )
else:
    mr_ind_verdict = (
        "DOES NOT PASS INDEPENDENT MEAN-REVERSION VALIDATION"
    )

print(f"Verdict: {mr_ind_verdict}")
print("RULES WERE NOT CHANGED FOR THIS TEST")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

pd.DataFrame([{
    "development_accuracy": round(mr_best_accuracy, 3),
    "development_signals": mr_best_signals,
    "independent_accuracy": round(ind_mr_accuracy, 3),
    "independent_signals": len(ind_mr_signals),
    "accuracy_change": round(mr_accuracy_change, 3),
    "avg_directional_return": round(ind_mr_avg_return, 5),
    "median_directional_return": round(ind_mr_median_return, 5),
    "passed": mr_independent_pass,
    "verdict": mr_ind_verdict,
}]).to_csv(
    "spy_sentinel_mean_reversion_independent.csv",
    index=False
)

print("Independent mean-reversion validation saved")

print("\nV4.2 THIRD-PERIOD BULLISH MEAN-REVERSION TEST")

third_end = datetime.now(timezone.utc) - timedelta(days=150)
third_start = third_end - timedelta(days=90)

third_request = StockBarsRequest(
    symbol_or_symbols=["SPY"],
    timeframe=TimeFrame(5, TimeFrameUnit.Minute),
    start=third_start,
    end=third_end,
    feed=DataFeed.IEX,
)

third = data.get_stock_bars(third_request).df

if isinstance(third.index, pd.MultiIndex):
    third = third.xs("SPY")

third = third.sort_index().copy()

print(f"Third-period bars loaded: {len(third)}")
print(f"Period start: {third_start.date()}")
print(f"Period end:   {third_end.date()}")

third.index = pd.to_datetime(
    third.index,
    utc=True
)

third["time_et"] = (
    third.index.tz_convert("America/New_York")
)

third["date_et"] = third["time_et"].dt.date
third["clock_et"] = third["time_et"].dt.time

from datetime import time

third = third[
    (third["clock_et"] >= time(9, 30))
    & (third["clock_et"] <= time(16, 0))
].copy()

print(f"Regular-session third-period bars: {len(third)}")

third["ema9"] = (
    third["close"].ewm(span=9, adjust=False).mean()
)

third["ema21"] = (
    third["close"].ewm(span=21, adjust=False).mean()
)

t_delta = third["close"].diff()
t_gain = t_delta.clip(lower=0)
t_loss = -t_delta.clip(upper=0)

t_avg_gain = t_gain.rolling(14).mean()
t_avg_loss = t_loss.rolling(14).mean()

t_rs = t_avg_gain / t_avg_loss.replace(0, np.nan)

third["rsi14"] = 100 - (100 / (1 + t_rs))

third["bb_mid"] = third["close"].rolling(20).mean()
third["bb_std"] = third["close"].rolling(20).std()

third["bb_upper"] = third["bb_mid"] + 2 * third["bb_std"]
third["bb_lower"] = third["bb_mid"] - 2 * third["bb_std"]

print("Third-period indicators calculated")

third["future_return_60m"] = np.where(
    third["date_et"] == third["date_et"].shift(-12),
    third["close"].shift(-12) / third["close"] - 1,
    np.nan
)

third["bull_reversion"] = (
    (third["close"] < third["bb_lower"])
    & (third["rsi14"] <= 40)
)

third_bull = third[
    third["bull_reversion"]
].dropna(
    subset=["future_return_60m"]
).copy()

print(f"Third-period bullish signals: {len(third_bull)}")

third_wins = (
    third_bull["future_return_60m"] > 0
)

third_accuracy = (
    third_wins.mean() * 100
    if len(third_bull)
    else 0.0
)

third_avg_return = (
    third_bull["future_return_60m"].mean() * 100
    if len(third_bull)
    else 0.0
)

third_median_return = (
    third_bull["future_return_60m"].median() * 100
    if len(third_bull)
    else 0.0
)

print("\nTHIRD-PERIOD RESULTS")
print(f"Signals:        {len(third_bull)}")
print(f"Accuracy:       {third_accuracy:.2f}%")
print(f"Average return: {third_avg_return:+.4f}%")
print(f"Median return:  {third_median_return:+.4f}%")

print("\nTHIRD-PERIOD WILSON INTERVAL")

n_third = len(third_bull)
wins_third = int(third_wins.sum())

if n_third > 0:

    p_third = wins_third / n_third
    z = 1.96

    denom = 1 + z**2 / n_third

    center = (
        p_third + z**2 / (2 * n_third)
    ) / denom

    margin = (
        z * np.sqrt(
            p_third * (1 - p_third) / n_third
            + z**2 / (4 * n_third**2)
        ) / denom
    )

    third_ci_low = center - margin
    third_ci_high = center + margin

else:

    third_ci_low = 0
    third_ci_high = 0

print(f"95% CI low:  {third_ci_low * 100:.2f}%")
print(f"95% CI high: {third_ci_high * 100:.2f}%")
print(f"CI above 50%: {third_ci_low > 0.50}")

print("\nV4.2 THIRD-PERIOD VERDICT")

third_pass = (
    len(third_bull) >= 100
    and third_accuracy >= 55
    and third_avg_return > 0
)

if third_pass:
    third_verdict = (
        "BULLISH MEAN REVERSION PASSES THIRD-PERIOD TEST"
    )
else:
    third_verdict = (
        "BULLISH MEAN REVERSION DOES NOT PASS THIRD-PERIOD TEST"
    )

print(f"Verdict: {third_verdict}")
print("THIS PERIOD WAS NOT USED TO SELECT THE RULE")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

pd.DataFrame([{
    "signals": len(third_bull),
    "accuracy": round(third_accuracy, 3),
    "avg_return": round(third_avg_return, 5),
    "median_return": round(third_median_return, 5),
    "ci_low": round(third_ci_low * 100, 3),
    "ci_high": round(third_ci_high * 100, 3),
    "passed": third_pass,
    "verdict": third_verdict,
}]).to_csv(
    "spy_sentinel_third_period_bullish_mr.csv",
    index=False
)

print("Third-period validation saved")

print("\nV4.3 OPENING-RANGE BREAKOUT DEVELOPMENT")

orb = clean.copy()

orb["minutes_et"] = (
    orb["time_et"].dt.hour * 60
    + orb["time_et"].dt.minute
)

opening_range = orb[
    (orb["minutes_et"] >= 570)
    & (orb["minutes_et"] < 600)
].groupby("date_et").agg(
    opening_high=("high", "max"),
    opening_low=("low", "min")
)

orb = orb.join(
    opening_range,
    on="date_et"
)

print("30-minute opening ranges calculated")

orb["bull_orb"] = (
    (orb["minutes_et"] >= 600)
    & (orb["close"] > orb["opening_high"])
    & (orb["volume_ratio"] >= 1.2)
)

orb["bear_orb"] = (
    (orb["minutes_et"] >= 600)
    & (orb["close"] < orb["opening_low"])
    & (orb["volume_ratio"] >= 1.2)
)

orb["orb_signal"] = np.where(
    orb["bull_orb"],
    "BULLISH",
    np.where(
        orb["bear_orb"],
        "BEARISH",
        "NO TRADE"
    )
)

print("Opening-range breakout signals generated")

orb_signals = orb[
    orb["orb_signal"].isin(
        ["BULLISH", "BEARISH"]
    )
].dropna(
    subset=["future_return_60m"]
).copy()

print(f"ORB signals: {len(orb_signals)}")

orb_correct = (
    (
        (orb_signals["orb_signal"] == "BULLISH")
        & (orb_signals["future_return_60m"] > 0)
    )
    |
    (
        (orb_signals["orb_signal"] == "BEARISH")
        & (orb_signals["future_return_60m"] < 0)
    )
)

orb_accuracy = (
    orb_correct.mean() * 100
    if len(orb_signals)
    else 0.0
)

print("\nORB ACCURACY")
print(f"Accuracy: {orb_accuracy:.2f}%")
print(f"Signals:  {len(orb_signals)}")
print(f"Edge:     {orb_accuracy - 50:+.2f}%")

orb_signed = np.where(
    orb_signals["orb_signal"] == "BULLISH",
    orb_signals["future_return_60m"],
    -orb_signals["future_return_60m"]
)

orb_avg_return = (
    float(np.mean(orb_signed)) * 100
    if len(orb_signed)
    else 0.0
)

orb_median_return = (
    float(np.median(orb_signed)) * 100
    if len(orb_signed)
    else 0.0
)

print("\nORB RETURN QUALITY")
print(f"Average directional return: {orb_avg_return:+.4f}%")
print(f"Median directional return:  {orb_median_return:+.4f}%")

print("\nORB DIRECTION SPLIT")

for direction in ["BULLISH", "BEARISH"]:

    d = orb_signals[
        orb_signals["orb_signal"] == direction
    ].copy()

    if direction == "BULLISH":
        correct = d["future_return_60m"] > 0
    else:
        correct = d["future_return_60m"] < 0

    accuracy = (
        correct.mean() * 100
        if len(d)
        else 0.0
    )

    print(
        f"{direction}: "
        f"{accuracy:.1f}% | "
        f"{len(d)} signals"
    )

print("\nV4.3 DEVELOPMENT GATE")

orb_candidate = (
    len(orb_signals) >= 50
    and orb_accuracy >= 55
    and orb_avg_return > 0
)

if orb_candidate:
    orb_verdict = "READY FOR INDEPENDENT TEST"
else:
    orb_verdict = "NOT STRONG ENOUGH"

print(f"Verdict: {orb_verdict}")
print("DEVELOPMENT DATA ONLY")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

pd.DataFrame([{
    "signals": len(orb_signals),
    "accuracy": round(orb_accuracy, 3),
    "avg_directional_return": round(orb_avg_return, 5),
    "median_directional_return": round(orb_median_return, 5),
    "candidate": orb_candidate,
    "verdict": orb_verdict,
}]).to_csv(
    "spy_sentinel_orb_development.csv",
    index=False
)

print("ORB development saved")

print("\nV4.4 PULLBACK-CONTINUATION DEVELOPMENT")

pb = clean.copy()

pb["ema50"] = (
    pb["close"]
    .ewm(span=50, adjust=False)
    .mean()
)

pb["ema50_slope5"] = (
    pb["ema50"] - pb["ema50"].shift(5)
).shift(1)

pb["distance_ema9"] = (
    (pb["close"] - pb["ema9"])
    / pb["close"]
)

print("Pullback trend features calculated")

pb["bull_trend"] = (
    (pb["close"] > pb["ema50"])
    & (pb["ema50_slope5"] > 0)
    & (pb["ema9"] > pb["ema21"])
)

pb["bear_trend"] = (
    (pb["close"] < pb["ema50"])
    & (pb["ema50_slope5"] < 0)
    & (pb["ema9"] < pb["ema21"])
)

pb["bull_pullback"] = (
    pb["bull_trend"]
    & (pb["distance_ema9"] <= 0)
    & (pb["close"] >= pb["vwap"] * 0.997)
)

pb["bear_pullback"] = (
    pb["bear_trend"]
    & (pb["distance_ema9"] >= 0)
    & (pb["close"] <= pb["vwap"] * 1.003)
)

print("Pullback conditions calculated")

pb["pullback_signal"] = np.where(
    pb["bull_pullback"],
    "BULLISH",
    np.where(
        pb["bear_pullback"],
        "BEARISH",
        "NO TRADE"
    )
)

pb_signals = pb[
    pb["pullback_signal"].isin(
        ["BULLISH", "BEARISH"]
    )
].dropna(
    subset=["future_return_60m"]
).copy()

print(f"Pullback signals: {len(pb_signals)}")

pb_correct = (
    (
        (pb_signals["pullback_signal"] == "BULLISH")
        & (pb_signals["future_return_60m"] > 0)
    )
    |
    (
        (pb_signals["pullback_signal"] == "BEARISH")
        & (pb_signals["future_return_60m"] < 0)
    )
)

pb_accuracy = (
    pb_correct.mean() * 100
    if len(pb_signals)
    else 0.0
)

print("\nPULLBACK ACCURACY")
print(f"Accuracy: {pb_accuracy:.2f}%")
print(f"Signals:  {len(pb_signals)}")
print(f"Edge:     {pb_accuracy - 50:+.2f}%")

pb_signed = np.where(
    pb_signals["pullback_signal"] == "BULLISH",
    pb_signals["future_return_60m"],
    -pb_signals["future_return_60m"]
)

pb_avg_return = (
    float(np.mean(pb_signed)) * 100
    if len(pb_signed)
    else 0.0
)

pb_median_return = (
    float(np.median(pb_signed)) * 100
    if len(pb_signed)
    else 0.0
)

print("\nPULLBACK RETURN QUALITY")
print(f"Average directional return: {pb_avg_return:+.4f}%")
print(f"Median directional return:  {pb_median_return:+.4f}%")

print("\nPULLBACK DIRECTION SPLIT")

for direction in ["BULLISH", "BEARISH"]:

    d = pb_signals[
        pb_signals["pullback_signal"] == direction
    ].copy()

    if direction == "BULLISH":
        correct = d["future_return_60m"] > 0
    else:
        correct = d["future_return_60m"] < 0

    acc = (
        correct.mean() * 100
        if len(d)
        else 0.0
    )

    print(
        f"{direction}: "
        f"{acc:.1f}% | "
        f"{len(d)} signals"
    )

print("\nV4.4 DEVELOPMENT GATE")

pb_candidate = (
    len(pb_signals) >= 50
    and pb_accuracy >= 55
    and pb_avg_return > 0
)

if pb_candidate:
    pb_verdict = "READY FOR INDEPENDENT TEST"
else:
    pb_verdict = "NOT STRONG ENOUGH"

print(f"Verdict: {pb_verdict}")
print("DEVELOPMENT DATA ONLY")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

pd.DataFrame([{
    "signals": len(pb_signals),
    "accuracy": round(pb_accuracy, 3),
    "avg_directional_return": round(pb_avg_return, 5),
    "median_directional_return": round(pb_median_return, 5),
    "candidate": pb_candidate,
    "verdict": pb_verdict,
}]).to_csv(
    "spy_sentinel_pullback_development.csv",
    index=False
)

print("Pullback development saved")

print("\nV4.5 BEARISH-PULLBACK INDEPENDENT TEST")

ind_pb = independent.copy()

ind_pb["future_return_60m_true"] = np.where(
    ind_pb["date_et"] == ind_pb["date_et"].shift(-12),
    ind_pb["close"].shift(-12) / ind_pb["close"] - 1,
    np.nan
)

print("True independent 60-minute returns calculated")

ind_pb["ema50"] = (
    ind_pb["close"]
    .ewm(span=50, adjust=False)
    .mean()
)

ind_pb["ema50_slope5"] = (
    ind_pb["ema50"]
    - ind_pb["ema50"].shift(5)
).shift(1)

ind_pb["distance_ema9"] = (
    (ind_pb["close"] - ind_pb["ema9"])
    / ind_pb["close"]
)

print("Independent pullback features calculated")

ind_pb["bear_trend"] = (
    (ind_pb["close"] < ind_pb["ema50"])
    & (ind_pb["ema50_slope5"] < 0)
    & (ind_pb["ema9"] < ind_pb["ema21"])
)

ind_pb["bear_pullback"] = (
    ind_pb["bear_trend"]
    & (ind_pb["distance_ema9"] >= 0)
    & (ind_pb["close"] <= ind_pb["vwap"] * 1.003)
)

ind_pb_bear = ind_pb[
    ind_pb["bear_pullback"]
].dropna(
    subset=["future_return_60m_true"]
).copy()

print(
    f"Independent bearish pullback signals: "
    f"{len(ind_pb_bear)}"
)

bear_pb_wins = (
    ind_pb_bear["future_return_60m_true"] < 0
)

bear_pb_accuracy = (
    bear_pb_wins.mean() * 100
    if len(ind_pb_bear)
    else 0.0
)

print("\nBEARISH-PULLBACK ACCURACY")
print(f"Accuracy: {bear_pb_accuracy:.2f}%")
print(f"Signals:  {len(ind_pb_bear)}")
print(f"Edge:     {bear_pb_accuracy - 50:+.2f}%")

bear_pb_directional_returns = (
    -ind_pb_bear["future_return_60m_true"]
)

bear_pb_avg_return = (
    bear_pb_directional_returns.mean() * 100
    if len(ind_pb_bear)
    else 0.0
)

bear_pb_median_return = (
    bear_pb_directional_returns.median() * 100
    if len(ind_pb_bear)
    else 0.0
)

print("\nBEARISH-PULLBACK RETURN QUALITY")
print(f"Average directional return: {bear_pb_avg_return:+.4f}%")
print(f"Median directional return:  {bear_pb_median_return:+.4f}%")

print("\nBEARISH-PULLBACK WILSON INTERVAL")

n_pb = len(ind_pb_bear)
wins_pb = int(bear_pb_wins.sum())

if n_pb > 0:

    p_pb = wins_pb / n_pb
    z = 1.96

    denominator = 1 + z**2 / n_pb

    center = (
        p_pb + z**2 / (2 * n_pb)
    ) / denominator

    margin = (
        z * np.sqrt(
            p_pb * (1 - p_pb) / n_pb
            + z**2 / (4 * n_pb**2)
        ) / denominator
    )

    pb_ci_low = center - margin
    pb_ci_high = center + margin

else:

    pb_ci_low = 0
    pb_ci_high = 0

print(f"95% CI low:  {pb_ci_low * 100:.2f}%")
print(f"95% CI high: {pb_ci_high * 100:.2f}%")
print(f"CI above 50%: {pb_ci_low > 0.50}")

development_bear_pb_accuracy = 57.0

bear_pb_change = (
    bear_pb_accuracy
    - development_bear_pb_accuracy
)

bear_pb_pass = (
    len(ind_pb_bear) >= 100
    and bear_pb_accuracy >= 55
    and bear_pb_avg_return > 0
    and abs(bear_pb_change) <= 10
)

print("\nV4.5 INDEPENDENT VERDICT")

print(
    f"Development bearish accuracy: "
    f"{development_bear_pb_accuracy:.2f}%"
)

print(
    f"Independent bearish accuracy: "
    f"{bear_pb_accuracy:.2f}%"
)

print(f"Change: {bear_pb_change:+.2f}%")

if bear_pb_pass:
    bear_pb_verdict = (
        "PASSES BEARISH-PULLBACK INDEPENDENT VALIDATION"
    )
else:
    bear_pb_verdict = (
        "DOES NOT PASS BEARISH-PULLBACK INDEPENDENT VALIDATION"
    )

print(f"Verdict: {bear_pb_verdict}")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

pd.DataFrame([{
    "development_accuracy": development_bear_pb_accuracy,
    "independent_signals": len(ind_pb_bear),
    "independent_accuracy": round(bear_pb_accuracy, 3),
    "accuracy_change": round(bear_pb_change, 3),
    "avg_directional_return": round(bear_pb_avg_return, 5),
    "median_directional_return": round(bear_pb_median_return, 5),
    "ci_low": round(pb_ci_low * 100, 3),
    "ci_high": round(pb_ci_high * 100, 3),
    "passed": bear_pb_pass,
    "verdict": bear_pb_verdict,
}]).to_csv(
    "spy_sentinel_bearish_pullback_independent.csv",
    index=False
)

print("Bearish-pullback independent validation saved")

print("\nV4.6 SPY + QQQ CONFIRMATION DEVELOPMENT")

qqq_request = StockBarsRequest(
    symbol_or_symbols=["QQQ"],
    timeframe=TimeFrame(5, TimeFrameUnit.Minute),
    start=research_start,
    end=research_end,
    feed=DataFeed.IEX,
)

qqq = data.get_stock_bars(qqq_request).df

if isinstance(qqq.index, pd.MultiIndex):
    qqq = qqq.xs("QQQ")

qqq = qqq.sort_index().copy()

print(f"QQQ development bars loaded: {len(qqq)}")

qqq.index = pd.to_datetime(
    qqq.index,
    utc=True
)

qqq["ema20"] = (
    qqq["close"]
    .ewm(span=20, adjust=False)
    .mean()
)

qqq["ema50"] = (
    qqq["close"]
    .ewm(span=50, adjust=False)
    .mean()
)

qqq["qqq_bull"] = (
    (qqq["close"] > qqq["ema20"])
    & (qqq["ema20"] > qqq["ema50"])
)

qqq["qqq_bear"] = (
    (qqq["close"] < qqq["ema20"])
    & (qqq["ema20"] < qqq["ema50"])
)

print("QQQ trend features calculated")

cross_dev = clean.copy()

cross_dev = cross_dev.join(
    qqq[
        [
            "close",
            "ema20",
            "ema50",
            "qqq_bull",
            "qqq_bear",
        ]
    ].rename(
        columns={
            "close": "qqq_close",
            "ema20": "qqq_ema20",
            "ema50": "qqq_ema50",
        }
    ),
    how="left"
)

cross_dev = cross_dev.dropna(
    subset=[
        "qqq_close",
        "qqq_ema20",
        "qqq_ema50",
    ]
)

print(f"Aligned SPY/QQQ bars: {len(cross_dev)}")

cross_dev["cross_match"] = (
    (
        (cross_dev["signal"] == "BULLISH")
        & cross_dev["qqq_bull"]
    )
    |
    (
        (cross_dev["signal"] == "BEARISH")
        & cross_dev["qqq_bear"]
    )
)

cross_signals = cross_dev[
    cross_dev["signal"].isin(
        ["BULLISH", "BEARISH"]
    )
    & cross_dev["cross_match"]
    & (
        (
            (cross_dev["signal"] == "BULLISH")
            & (cross_dev["close"] > cross_dev["vwap"])
        )
        |
        (
            (cross_dev["signal"] == "BEARISH")
            & (cross_dev["close"] < cross_dev["vwap"])
        )
    )
].dropna(
    subset=["future_return_60m"]
).copy()

print(f"Cross-market signals: {len(cross_signals)}")

cross_correct = (
    (
        (cross_signals["signal"] == "BULLISH")
        & (cross_signals["future_return_60m"] > 0)
    )
    |
    (
        (cross_signals["signal"] == "BEARISH")
        & (cross_signals["future_return_60m"] < 0)
    )
)

cross_accuracy = (
    cross_correct.mean() * 100
    if len(cross_signals)
    else 0.0
)

print("\nCROSS-MARKET ACCURACY")
print(f"Accuracy: {cross_accuracy:.2f}%")
print(f"Signals:  {len(cross_signals)}")
print(f"Edge:     {cross_accuracy - 50:+.2f}%")

cross_signed = np.where(
    cross_signals["signal"] == "BULLISH",
    cross_signals["future_return_60m"],
    -cross_signals["future_return_60m"]
)

cross_avg_return = (
    float(np.mean(cross_signed)) * 100
    if len(cross_signed)
    else 0.0
)

cross_median_return = (
    float(np.median(cross_signed)) * 100
    if len(cross_signed)
    else 0.0
)

print("\nCROSS-MARKET RETURN QUALITY")
print(
    f"Average directional return: "
    f"{cross_avg_return:+.4f}%"
)
print(
    f"Median directional return:  "
    f"{cross_median_return:+.4f}%"
)

print("\nCROSS-MARKET DIRECTION SPLIT")

for direction in ["BULLISH", "BEARISH"]:

    d = cross_signals[
        cross_signals["signal"] == direction
    ]

    if direction == "BULLISH":
        correct = d["future_return_60m"] > 0
    else:
        correct = d["future_return_60m"] < 0

    acc = (
        correct.mean() * 100
        if len(d)
        else 0.0
    )

    print(
        f"{direction}: "
        f"{acc:.1f}% | "
        f"{len(d)} signals"
    )

print("\nV4.6 DEVELOPMENT GATE")

cross_candidate = (
    len(cross_signals) >= 100
    and cross_accuracy >= 55
    and cross_avg_return > 0
)

if cross_candidate:
    cross_verdict = "READY FOR INDEPENDENT TEST"
else:
    cross_verdict = "NOT STRONG ENOUGH"

print(f"Verdict: {cross_verdict}")
print("DEVELOPMENT DATA ONLY")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

pd.DataFrame([{
    "signals": len(cross_signals),
    "accuracy": round(cross_accuracy, 3),
    "avg_return": round(cross_avg_return, 5),
    "median_return": round(cross_median_return, 5),
    "candidate": cross_candidate,
    "verdict": cross_verdict,
}]).to_csv(
    "spy_sentinel_spy_qqq_development.csv",
    index=False
)

print("SPY/QQQ research saved")

print("\nV4.6 DEVELOPMENT GATE")

cross_candidate = (
    len(cross_signals) >= 100
    and cross_accuracy >= 55
    and cross_avg_return > 0
)

if cross_candidate:
    cross_verdict = "READY FOR INDEPENDENT TEST"
else:
    cross_verdict = "NOT STRONG ENOUGH"

print(f"Verdict: {cross_verdict}")
print("DEVELOPMENT DATA ONLY")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

pd.DataFrame([{
    "signals": len(cross_signals),
    "accuracy": round(cross_accuracy, 3),
    "avg_return": round(cross_avg_return, 5),
    "median_return": round(cross_median_return, 5),
    "candidate": cross_candidate,
    "verdict": cross_verdict,
}]).to_csv(
    "spy_sentinel_spy_qqq_development.csv",
    index=False
)

print("SPY/QQQ research saved")

print("\nV4.7 INDEPENDENT SPY + QQQ TEST")

qqq_ind_request = StockBarsRequest(
    symbol_or_symbols=["QQQ"],
    timeframe=TimeFrame(5, TimeFrameUnit.Minute),
    start=independent_start,
    end=independent_end,
    feed=DataFeed.IEX,
)

qqq_ind = data.get_stock_bars(qqq_ind_request).df

if isinstance(qqq_ind.index, pd.MultiIndex):
    qqq_ind = qqq_ind.xs("QQQ")

qqq_ind = qqq_ind.sort_index().copy()

print(f"Independent QQQ bars loaded: {len(qqq_ind)}")

qqq_ind.index = pd.to_datetime(
    qqq_ind.index,
    utc=True
)

qqq_ind["ema20"] = (
    qqq_ind["close"]
    .ewm(span=20, adjust=False)
    .mean()
)

qqq_ind["ema50"] = (
    qqq_ind["close"]
    .ewm(span=50, adjust=False)
    .mean()
)

qqq_ind["qqq_bull"] = (
    (qqq_ind["close"] > qqq_ind["ema20"])
    & (qqq_ind["ema20"] > qqq_ind["ema50"])
)

qqq_ind["qqq_bear"] = (
    (qqq_ind["close"] < qqq_ind["ema20"])
    & (qqq_ind["ema20"] < qqq_ind["ema50"])
)

print("Independent QQQ trend features calculated")

cross_ind = independent.copy()

cross_ind["future_return_60m_true"] = np.where(
    cross_ind["date_et"]
    == cross_ind["date_et"].shift(-12),
    cross_ind["close"].shift(-12)
    / cross_ind["close"]
    - 1,
    np.nan
)

cross_ind = cross_ind.join(
    qqq_ind[
        [
            "close",
            "ema20",
            "ema50",
            "qqq_bull",
            "qqq_bear",
        ]
    ].rename(
        columns={
            "close": "qqq_close",
            "ema20": "qqq_ema20",
            "ema50": "qqq_ema50",
        }
    ),
    how="left"
)

print("Independent SPY/QQQ data aligned")

cross_ind["cross_match"] = (
    (
        (cross_ind["signal"] == "BULLISH")
        & cross_ind["qqq_bull"]
    )
    |
    (
        (cross_ind["signal"] == "BEARISH")
        & cross_ind["qqq_bear"]
    )
)

cross_ind_signals = cross_ind[
    cross_ind["signal"].isin(
        ["BULLISH", "BEARISH"]
    )
    & cross_ind["cross_match"]
    & (
        (
            (cross_ind["signal"] == "BULLISH")
            & (cross_ind["close"] > cross_ind["vwap"])
        )
        |
        (
            (cross_ind["signal"] == "BEARISH")
            & (cross_ind["close"] < cross_ind["vwap"])
        )
    )
].dropna(
    subset=["future_return_60m_true"]
).copy()

print(
    f"Independent cross-market signals: "
    f"{len(cross_ind_signals)}"
)

cross_ind_correct = (
    (
        (cross_ind_signals["signal"] == "BULLISH")
        & (cross_ind_signals["future_return_60m_true"] > 0)
    )
    |
    (
        (cross_ind_signals["signal"] == "BEARISH")
        & (cross_ind_signals["future_return_60m_true"] < 0)
    )
)

cross_ind_accuracy = (
    cross_ind_correct.mean() * 100
    if len(cross_ind_signals)
    else 0.0
)

print("\nINDEPENDENT CROSS-MARKET ACCURACY")
print(f"Accuracy: {cross_ind_accuracy:.2f}%")
print(f"Signals:  {len(cross_ind_signals)}")
print(f"Edge:     {cross_ind_accuracy - 50:+.2f}%")

cross_ind_signed = np.where(
    cross_ind_signals["signal"] == "BULLISH",
    cross_ind_signals["future_return_60m_true"],
    -cross_ind_signals["future_return_60m_true"]
)

cross_ind_avg_return = (
    float(np.mean(cross_ind_signed)) * 100
    if len(cross_ind_signed)
    else 0.0
)

cross_ind_median_return = (
    float(np.median(cross_ind_signed)) * 100
    if len(cross_ind_signed)
    else 0.0
)

print("\nINDEPENDENT RETURN QUALITY")
print(
    f"Average directional return: "
    f"{cross_ind_avg_return:+.4f}%"
)
print(
    f"Median directional return:  "
    f"{cross_ind_median_return:+.4f}%"
)

cross_ind_signed = np.where(
    cross_ind_signals["signal"] == "BULLISH",
    cross_ind_signals["future_return_60m_true"],
    -cross_ind_signals["future_return_60m_true"]
)

cross_ind_avg_return = (
    float(np.mean(cross_ind_signed)) * 100
    if len(cross_ind_signed)
    else 0.0
)

cross_ind_median_return = (
    float(np.median(cross_ind_signed)) * 100
    if len(cross_ind_signed)
    else 0.0
)

print("\nINDEPENDENT RETURN QUALITY")
print(
    f"Average directional return: "
    f"{cross_ind_avg_return:+.4f}%"
)
print(
    f"Median directional return:  "
    f"{cross_ind_median_return:+.4f}%"
)

cross_accuracy_change = (
    cross_ind_accuracy - cross_accuracy
)

cross_independent_pass = (
    len(cross_ind_signals) >= 100
    and cross_ind_accuracy >= 55
    and cross_ind_avg_return > 0
    and abs(cross_accuracy_change) <= 10
)

print("\nV4.7 INDEPENDENT VERDICT")

print(f"Development accuracy: {cross_accuracy:.2f}%")
print(f"Independent accuracy: {cross_ind_accuracy:.2f}%")
print(f"Change:               {cross_accuracy_change:+.2f}%")

if cross_independent_pass:
    cross_ind_verdict = (
        "PASSES INDEPENDENT SPY-QQQ VALIDATION"
    )
else:
    cross_ind_verdict = (
        "DOES NOT PASS INDEPENDENT SPY-QQQ VALIDATION"
    )

print(f"Verdict: {cross_ind_verdict}")
print("RULES WERE NOT CHANGED FOR THIS TEST")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

pd.DataFrame([{
    "development_signals": len(cross_signals),
    "development_accuracy": round(cross_accuracy, 3),
    "independent_signals": len(cross_ind_signals),
    "independent_accuracy": round(cross_ind_accuracy, 3),
    "accuracy_change": round(cross_accuracy_change, 3),
    "avg_directional_return": round(cross_ind_avg_return, 5),
    "median_directional_return": round(cross_ind_median_return, 5),
    "passed": cross_independent_pass,
    "verdict": cross_ind_verdict,
}]).to_csv(
    "spy_sentinel_spy_qqq_independent.csv",
    index=False
)

print("Independent SPY/QQQ validation saved")

print("\nV4.8 SPY-vs-QQQ RELATIVE-STRENGTH DEVELOPMENT")

rs = clean.copy()

rs = rs.join(
    qqq[["close"]].rename(
        columns={"close": "qqq_close"}
    ),
    how="left"
)

rs = rs.dropna(
    subset=["qqq_close"]
).copy()

print(f"Aligned development bars: {len(rs)}")

rs["spy_ret30"] = (
    rs["close"].pct_change(6).shift(1)
)

rs["qqq_ret30"] = (
    rs["qqq_close"].pct_change(6).shift(1)
)

rs["relative_strength"] = (
    rs["spy_ret30"] - rs["qqq_ret30"]
)

print("Lagged 30-minute relative-strength feature calculated")

RS_THRESHOLD = 0.001

rs["rs_bull"] = (
    (rs["spy_ret30"] > 0)
    & (rs["qqq_ret30"] > 0)
    & (rs["relative_strength"] >= RS_THRESHOLD)
)

rs["rs_bear"] = (
    (rs["spy_ret30"] < 0)
    & (rs["qqq_ret30"] < 0)
    & (rs["relative_strength"] <= -RS_THRESHOLD)
)

rs["rs_signal"] = np.where(
    rs["rs_bull"],
    "BULLISH",
    np.where(
        rs["rs_bear"],
        "BEARISH",
        "NO TRADE"
    )
)

print("Relative-strength signals generated")

rs_signals = rs[
    rs["rs_signal"].isin(
        ["BULLISH", "BEARISH"]
    )
].dropna(
    subset=["future_return_60m"]
).copy()

print(f"Relative-strength signals: {len(rs_signals)}")

rs_correct = (
    (
        (rs_signals["rs_signal"] == "BULLISH")
        & (rs_signals["future_return_60m"] > 0)
    )
    |
    (
        (rs_signals["rs_signal"] == "BEARISH")
        & (rs_signals["future_return_60m"] < 0)
    )
)

rs_accuracy = (
    rs_correct.mean() * 100
    if len(rs_signals)
    else 0.0
)

print("\nRELATIVE-STRENGTH ACCURACY")
print(f"Accuracy: {rs_accuracy:.2f}%")
print(f"Signals:  {len(rs_signals)}")
print(f"Edge:     {rs_accuracy - 50:+.2f}%")

rs_signed = np.where(
    rs_signals["rs_signal"] == "BULLISH",
    rs_signals["future_return_60m"],
    -rs_signals["future_return_60m"]
)

rs_avg_return = (
    float(np.mean(rs_signed)) * 100
    if len(rs_signed)
    else 0.0
)

rs_median_return = (
    float(np.median(rs_signed)) * 100
    if len(rs_signed)
    else 0.0
)

print("\nRELATIVE-STRENGTH RETURN QUALITY")
print(f"Average directional return: {rs_avg_return:+.4f}%")
print(f"Median directional return:  {rs_median_return:+.4f}%")

print("\nRELATIVE-STRENGTH DIRECTION SPLIT")

for direction in ["BULLISH", "BEARISH"]:

    d = rs_signals[
        rs_signals["rs_signal"] == direction
    ].copy()

    if direction == "BULLISH":
        correct = d["future_return_60m"] > 0
    else:
        correct = d["future_return_60m"] < 0

    acc = (
        correct.mean() * 100
        if len(d)
        else 0.0
    )

    print(
        f"{direction}: "
        f"{acc:.1f}% | "
        f"{len(d)} signals"
    )

print("\nV4.8 DEVELOPMENT GATE")

rs_candidate = (
    len(rs_signals) >= 100
    and rs_accuracy >= 55
    and rs_avg_return > 0
)

if rs_candidate:
    rs_verdict = "READY FOR INDEPENDENT TEST"
else:
    rs_verdict = "NOT STRONG ENOUGH"

print(f"Threshold: {RS_THRESHOLD * 100:.2f}%")
print(f"Verdict:   {rs_verdict}")
print("DEVELOPMENT DATA ONLY")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

pd.DataFrame([{
    "threshold": RS_THRESHOLD,
    "signals": len(rs_signals),
    "accuracy": round(rs_accuracy, 3),
    "avg_return": round(rs_avg_return, 5),
    "median_return": round(rs_median_return, 5),
    "candidate": rs_candidate,
    "verdict": rs_verdict,
}]).to_csv(
    "spy_sentinel_relative_strength_development.csv",
    index=False
)

print("Relative-strength development saved")

print("\nV5.0 MACHINE-LEARNING DEVELOPMENT")

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score

ml = clean.copy()

ml["mom15"] = ml["close"].pct_change(3).shift(1)
ml["mom30"] = ml["close"].pct_change(6).shift(1)
ml["mom60"] = ml["close"].pct_change(12).shift(1)

ml["ema9_distance"] = (
    (ml["close"] - ml["ema9"]) / ml["close"]
)

ml["ema21_distance"] = (
    (ml["close"] - ml["ema21"]) / ml["close"]
)

ml["vwap_distance"] = (
    (ml["close"] - ml["vwap"]) / ml["close"]
)

ml["ema_spread"] = (
    (ml["ema9"] - ml["ema21"]) / ml["close"]
)

ml["minute_of_day"] = (
    ml["time_et"].dt.hour * 60
    + ml["time_et"].dt.minute
)

print("ML features created")

ML_FEATURES = [
    "rsi14",
    "volume_ratio",
    "mom15",
    "mom30",
    "mom60",
    "ema9_distance",
    "ema21_distance",
    "vwap_distance",
    "ema_spread",
    "minute_of_day",
]

ml["target"] = np.where(
    ml["future_return_60m"] > 0,
    1,
    0
)

ml_data = ml.dropna(
    subset=ML_FEATURES + ["future_return_60m"]
).copy()

X = ml_data[ML_FEATURES]
y = ml_data["target"]

print(f"ML development rows: {len(ml_data)}")
print(f"Features: {len(ML_FEATURES)}")

print("\nTIME-SERIES CROSS-VALIDATION")

tscv = TimeSeriesSplit(n_splits=5)

fold_results = []

for fold_number, (train_idx, test_idx) in enumerate(
    tscv.split(X),
    start=1
):

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]

    y_train = y.iloc[train_idx]
    y_test = y.iloc[test_idx]

    model = Pipeline([
        ("scale", StandardScaler()),
        (
            "logistic",
            LogisticRegression(
                max_iter=2000,
                random_state=42
            )
        ),
    ])

    model.fit(X_train, y_train)

    prediction = model.predict(X_test)

    accuracy = accuracy_score(
        y_test,
        prediction
    ) * 100

    fold_results.append({
        "fold": fold_number,
        "train_rows": len(train_idx),
        "test_rows": len(test_idx),
        "accuracy": accuracy,
    })

    print(
        f"Fold {fold_number}: "
        f"{accuracy:.2f}% | "
        f"{len(test_idx)} test rows"
    )

fold_df = pd.DataFrame(fold_results)

ml_mean_accuracy = fold_df["accuracy"].mean()
ml_worst_accuracy = fold_df["accuracy"].min()
ml_best_accuracy = fold_df["accuracy"].max()

print("\nML STABILITY")

print(
    f"Mean CV accuracy:  "
    f"{ml_mean_accuracy:.2f}%"
)

print(
    f"Worst fold:        "
    f"{ml_worst_accuracy:.2f}%"
)

print(
    f"Best fold:         "
    f"{ml_best_accuracy:.2f}%"
)

print("\nHIGH-CONFIDENCE ML SIGNAL TEST")

confidence_results = []

for train_idx, test_idx in tscv.split(X):

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]

    y_train = y.iloc[train_idx]
    y_test = y.iloc[test_idx]

    model = Pipeline([
        ("scale", StandardScaler()),
        (
            "logistic",
            LogisticRegression(
                max_iter=2000,
                random_state=42
            )
        ),
    ])

    model.fit(X_train, y_train)

    probabilities = model.predict_proba(
        X_test
    )[:, 1]

    high_confidence = (
        (probabilities >= 0.60)
        | (probabilities <= 0.40)
    )

    selected_probs = probabilities[
        high_confidence
    ]

    selected_actual = y_test.to_numpy()[
        high_confidence
    ]

    if len(selected_probs) == 0:
        continue

    selected_prediction = (
        selected_probs >= 0.50
    ).astype(int)

    selected_accuracy = (
        selected_prediction
        == selected_actual
    ).mean() * 100

    confidence_results.append({
        "signals": len(selected_probs),
        "accuracy": selected_accuracy,
    })

print("\nHIGH-CONFIDENCE ML SIGNAL TEST")

confidence_results = []

for train_idx, test_idx in tscv.split(X):

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]

    y_train = y.iloc[train_idx]
    y_test = y.iloc[test_idx]

    model = Pipeline([
        ("scale", StandardScaler()),
        (
            "logistic",
            LogisticRegression(
                max_iter=2000,
                random_state=42
            )
        ),
    ])

    model.fit(X_train, y_train)

    probabilities = model.predict_proba(
        X_test
    )[:, 1]

    high_confidence = (
        (probabilities >= 0.60)
        | (probabilities <= 0.40)
    )

    selected_probs = probabilities[
        high_confidence
    ]

    selected_actual = y_test.to_numpy()[
        high_confidence
    ]

    if len(selected_probs) == 0:
        continue

    selected_prediction = (
        selected_probs >= 0.50
    ).astype(int)

    selected_accuracy = (
        selected_prediction
        == selected_actual
    ).mean() * 100

    confidence_results.append({
        "signals": len(selected_probs),
        "accuracy": selected_accuracy,
    })

confidence_df = pd.DataFrame(
    confidence_results
)

if not confidence_df.empty:

    hc_signals = int(
        confidence_df["signals"].sum()
    )

    hc_accuracy = np.average(
        confidence_df["accuracy"],
        weights=confidence_df["signals"]
    )

else:

    hc_signals = 0
    hc_accuracy = 0.0

print(
    f"High-confidence signals: "
    f"{hc_signals}"
)

print(
    f"High-confidence accuracy: "
    f"{hc_accuracy:.2f}%"
)

print("\nV5.0 ML DEVELOPMENT GATE")

ml_candidate = (
    ml_mean_accuracy >= 52
    and ml_worst_accuracy >= 48
    and hc_accuracy >= 55
    and hc_signals >= 100
)

if ml_candidate:
    ml_verdict = (
        "ML CANDIDATE READY FOR INDEPENDENT TEST"
    )
else:
    ml_verdict = (
        "ML MODEL NOT STRONG ENOUGH"
    )

print(f"Verdict: {ml_verdict}")

print("INDEPENDENT PERIOD NOT USED FOR TRAINING")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

fold_df.to_csv(
    "spy_sentinel_ml_cv_results.csv",
    index=False
)

pd.DataFrame([{
    "mean_accuracy": round(
        ml_mean_accuracy, 3
    ),
    "worst_accuracy": round(
        ml_worst_accuracy, 3
    ),
    "best_accuracy": round(
        ml_best_accuracy, 3
    ),
    "high_confidence_signals": hc_signals,
    "high_confidence_accuracy": round(
        hc_accuracy, 3
    ),
    "candidate": ml_candidate,
    "verdict": ml_verdict,
}]).to_csv(
    "spy_sentinel_ml_development_summary.csv",
    index=False
)

print("ML development results saved")

print("\nV5.1 RANDOM-FOREST DEVELOPMENT")

from sklearn.ensemble import RandomForestClassifier

rf_fold_results = []
rf_confidence_results = []

print("Random Forest loaded")

print("\nRANDOM-FOREST TIME-SERIES CV")

for fold_number, (train_idx, test_idx) in enumerate(
    tscv.split(X),
    start=1
):

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]

    y_train = y.iloc[train_idx]
    y_test = y.iloc[test_idx]

    rf_model = RandomForestClassifier(
        n_estimators=300,
        max_depth=6,
        min_samples_leaf=20,
        random_state=42,
        n_jobs=-1
    )

    rf_model.fit(
        X_train,
        y_train
    )

    prediction = rf_model.predict(
        X_test
    )

    accuracy = accuracy_score(
        y_test,
        prediction
    ) * 100

    rf_fold_results.append({
        "fold": fold_number,
        "test_rows": len(test_idx),
        "accuracy": accuracy,
    })

    print(
        f"Fold {fold_number}: "
        f"{accuracy:.2f}% | "
        f"{len(test_idx)} rows"
    )

rf_fold_df = pd.DataFrame(
    rf_fold_results
)

rf_mean_accuracy = (
    rf_fold_df["accuracy"].mean()
)

rf_worst_accuracy = (
    rf_fold_df["accuracy"].min()
)

rf_best_accuracy = (
    rf_fold_df["accuracy"].max()
)

print("\nRANDOM-FOREST STABILITY")

print(
    f"Mean accuracy: {rf_mean_accuracy:.2f}%"
)

print(
    f"Worst fold:    {rf_worst_accuracy:.2f}%"
)

print(
    f"Best fold:     {rf_best_accuracy:.2f}%"
)

print("\nRF HIGH-CONFIDENCE TEST")

for train_idx, test_idx in tscv.split(X):

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]

    y_train = y.iloc[train_idx]
    y_test = y.iloc[test_idx]

    rf_model = RandomForestClassifier(
        n_estimators=300,
        max_depth=6,
        min_samples_leaf=20,
        random_state=42,
        n_jobs=-1
    )

    rf_model.fit(
        X_train,
        y_train
    )

    probabilities = rf_model.predict_proba(
        X_test
    )[:, 1]

    high_conf = (
        (probabilities >= 0.60)
        | (probabilities <= 0.40)
    )

    selected_probs = probabilities[
        high_conf
    ]

    selected_actual = y_test.to_numpy()[
        high_conf
    ]

    if len(selected_probs) == 0:
        continue

    selected_prediction = (
        selected_probs >= 0.50
    ).astype(int)

    selected_accuracy = (
        selected_prediction
        == selected_actual
    ).mean() * 100

    rf_confidence_results.append({
        "signals": len(selected_probs),
        "accuracy": selected_accuracy,
    })

rf_conf_df = pd.DataFrame(
    rf_confidence_results
)

if not rf_conf_df.empty:

    rf_hc_signals = int(
        rf_conf_df["signals"].sum()
    )

    rf_hc_accuracy = np.average(
        rf_conf_df["accuracy"],
        weights=rf_conf_df["signals"]
    )

else:

    rf_hc_signals = 0
    rf_hc_accuracy = 0.0

print(
    f"High-confidence signals: "
    f"{rf_hc_signals}"
)

print(
    f"High-confidence accuracy: "
    f"{rf_hc_accuracy:.2f}%"
)

print("\nRF FEATURE IMPORTANCE")

final_rf = RandomForestClassifier(
    n_estimators=300,
    max_depth=6,
    min_samples_leaf=20,
    random_state=42,
    n_jobs=-1
)

final_rf.fit(
    X,
    y
)

importance_df = pd.DataFrame({
    "feature": ML_FEATURES,
    "importance": final_rf.feature_importances_,
}).sort_values(
    "importance",
    ascending=False
)

print(
    importance_df.head(10).to_string(
        index=False
    )
)

print("\nV5.1 RF DEVELOPMENT GATE")

rf_candidate = (
    rf_mean_accuracy >= 52
    and rf_worst_accuracy >= 48
    and rf_hc_accuracy >= 55
    and rf_hc_signals >= 100
)

if rf_candidate:
    rf_verdict = (
        "RF CANDIDATE READY FOR INDEPENDENT TEST"
    )
else:
    rf_verdict = (
        "RF MODEL NOT STRONG ENOUGH"
    )

print(f"Verdict: {rf_verdict}")

print("INDEPENDENT PERIOD NOT USED")
print("PAPER TRADING: LOCKED")
print("LIVE TRADING: LOCKED")

rf_fold_df.to_csv(
    "spy_sentinel_rf_cv_results.csv",
    index=False
)

importance_df.to_csv(
    "spy_sentinel_rf_feature_importance.csv",
    index=False
)

pd.DataFrame([{
    "mean_accuracy": round(
        rf_mean_accuracy, 3
    ),
    "worst_accuracy": round(
        rf_worst_accuracy, 3
    ),
    "best_accuracy": round(
        rf_best_accuracy, 3
    ),
    "high_confidence_signals": rf_hc_signals,
    "high_confidence_accuracy": round(
        rf_hc_accuracy, 3
    ),
    "candidate": rf_candidate,
    "verdict": rf_verdict,
}]).to_csv(
    "spy_sentinel_rf_summary.csv",
    index=False
)

print("Random-Forest development saved")
