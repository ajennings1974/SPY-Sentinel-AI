import os
import json
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest

load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

EXECUTION_ENABLED = False
LIVE_TRADING_ENABLED = False

if not API_KEY or not SECRET_KEY:
    raise RuntimeError("Missing Alpaca API credentials")

print("\nSPY SENTINEL AI — V96 CLEAN AGENT")
print("================================")
print("Execution enabled:", EXECUTION_ENABLED)
print("Live trading enabled:", LIVE_TRADING_ENABLED)
print("Environment: ALPACA PAPER")

# --------------------------------------------------
# 1. PAPER ACCOUNT
# --------------------------------------------------

trading = TradingClient(
    API_KEY,
    SECRET_KEY,
    paper=True,
)

account = trading.get_account()

print("\nACCOUNT")
print("Status:", account.status)
print("Portfolio value:", account.portfolio_value)
print("Buying power:", account.buying_power)

# --------------------------------------------------
# 2. CURRENT SPY PRICE
# --------------------------------------------------

stock_data = StockHistoricalDataClient(
    API_KEY,
    SECRET_KEY,
)

latest_trade = stock_data.get_stock_latest_trade(
    StockLatestTradeRequest(
        symbol_or_symbols="SPY"
    )
)

spy_price = float(
    latest_trade["SPY"].price
)

print("\nMARKET")
print(f"SPY price: ${spy_price:.2f}")

# --------------------------------------------------
# 3. OPTIONS CONTRACTS
# --------------------------------------------------

headers = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY,
}

today = datetime.now().date()

contracts_url = (
    "https://paper-api.alpaca.markets"
    "/v2/options/contracts"
)

params = {
    "underlying_symbols": "SPY",
    "status": "active",
    "expiration_date_gte": today.isoformat(),
    "expiration_date_lte":
        (today + timedelta(days=10)).isoformat(),
    "strike_price_gte":
        round(spy_price * 0.97, 2),
    "strike_price_lte":
        round(spy_price * 1.03, 2),
    "limit": 100,
}

response = requests.get(
    contracts_url,
    headers=headers,
    params=params,
    timeout=20,
)

response.raise_for_status()

contracts = response.json().get(
    "option_contracts",
    []
)

print("\nOPTIONS")
print("Contracts found:", len(contracts))

if not contracts:
    print("DECISION: NO TRADE")
    print("Reason: No eligible SPY contracts found")
    raise SystemExit(0)

# --------------------------------------------------
# 4. RANK BY EXPIRATION + ATM DISTANCE
# --------------------------------------------------

def contract_score(c):

    strike = float(
        c["strike_price"]
    )

    exp = datetime.strptime(
        c["expiration_date"],
        "%Y-%m-%d",
    ).date()

    days = max(
        (exp - today).days,
        0,
    )

    atm_distance = abs(
        strike - spy_price
    ) / spy_price

    # Prefer 2–7 DTE and near ATM.
    dte_penalty = (
        abs(days - 4) / 10
    )

    return (
        atm_distance
        + dte_penalty
    )

contracts = [
    c for c in contracts
    if c.get("tradable", True)
]

contracts.sort(
    key=contract_score
)

shortlist = contracts[:20]

symbols = [
    c["symbol"]
    for c in shortlist
]

print("Shortlist:", len(symbols))

# --------------------------------------------------
# 5. OPTION SNAPSHOTS / GREEKS
# --------------------------------------------------

snapshots_url = (
    "https://data.alpaca.markets"
    "/v1beta1/options/snapshots"
)

snap_response = requests.get(
    snapshots_url,
    headers=headers,
    params={
        "symbols": ",".join(symbols),
        "limit": 100,
    },
    timeout=20,
)

snap_response.raise_for_status()

snapshots = snap_response.json().get(
    "snapshots",
    {}
)

ranked = []

for contract in shortlist:

    symbol = contract["symbol"]

    snap = snapshots.get(symbol)

    if not snap:
        continue

    quote = snap.get(
        "latestQuote",
        {}
    ) or {}

    greeks = snap.get(
        "greeks",
        {}
    ) or {}

    bid = quote.get("bp")
    ask = quote.get("ap")

    if bid is None or ask is None:
        continue

    bid = float(bid)
    ask = float(ask)

    if bid <= 0 or ask <= 0:
        continue

    mid = (
        bid + ask
    ) / 2

    spread = (
        ask - bid
    )

    spread_pct = (
        spread / mid
        if mid > 0
        else 999
    )

    delta = greeks.get("delta")

    strike = float(
        contract["strike_price"]
    )

    atm_pct = (
        abs(strike - spy_price)
        / spy_price
    )

    liquidity_pass = (
        spread_pct <= 0.20
    )

    atm_pass = (
        atm_pct <= 0.02
    )

    candidate_score = (
        atm_pct
        + spread_pct
    )

    ranked.append({
        "symbol": symbol,
        "type": contract.get("type"),
        "expiration":
            contract["expiration_date"],
        "strike": strike,
        "bid": bid,
        "ask": ask,
        "mid": mid,
        "spread_pct": spread_pct,
        "delta": delta,
        "atm_pct": atm_pct,
        "liquidity_pass":
            liquidity_pass,
        "atm_pass":
            atm_pass,
        "score":
            candidate_score,
    })

ranked.sort(
    key=lambda x: x["score"]
)

# --------------------------------------------------
# 6. RISK GATE
# --------------------------------------------------

eligible = [
    x for x in ranked
    if x["liquidity_pass"]
    and x["atm_pass"]
]

print("\nRISK GATE")
print(
    "Contracts with snapshots:",
    len(ranked)
)

print(
    "Eligible contracts:",
    len(eligible)
)

candidate = (
    eligible[0]
    if eligible
    else None
)

RESEARCH_EDGE_PROVEN = False

if candidate is None:

    decision = "NO TRADE"
    reason = (
        "No contract passed "
        "liquidity and ATM gates"
    )

elif not RESEARCH_EDGE_PROVEN:

    decision = "NO TRADE"
    reason = (
        "Contract found, but "
        "strategy edge is not proven"
    )

elif not EXECUTION_ENABLED:

    decision = "PAPER-READY"
    reason = (
        "Candidate passed gates, "
        "but execution remains disabled"
    )

else:

    decision = "EXECUTION PATH ENABLED"
    reason = (
        "Execution would occur here"
    )

# --------------------------------------------------
# 7. OUTPUT
# --------------------------------------------------

print("\nAGENT DECISION")
print("Decision:", decision)
print("Reason:", reason)

if candidate:

    print("\nBEST OPTIONS CANDIDATE")

    print(
        "Symbol:",
        candidate["symbol"],
    )

    print(
        "Type:",
        candidate["type"],
    )

    print(
        "Expiration:",
        candidate["expiration"],
    )

    print(
        "Strike:",
        candidate["strike"],
    )

    print(
        "Bid / Ask:",
        candidate["bid"],
        "/",
        candidate["ask"],
    )

    print(
        "Spread %:",
        round(
            candidate["spread_pct"]
            * 100,
            2,
        ),
    )

    print(
        "Delta:",
        candidate["delta"],
    )

# --------------------------------------------------
# 8. AUDIT LOG
# --------------------------------------------------

audit = {
    "timestamp_utc":
        datetime.now(
            timezone.utc
        ).isoformat(),
    "agent_version":
        "V96",
    "spy_price":
        spy_price,
    "contracts_found":
        len(contracts),
    "contracts_ranked":
        len(ranked),
    "eligible_contracts":
        len(eligible),
    "candidate":
        candidate,
    "research_edge_proven":
        RESEARCH_EDGE_PROVEN,
    "execution_enabled":
        EXECUTION_ENABLED,
    "live_trading_enabled":
        LIVE_TRADING_ENABLED,
    "decision":
        decision,
    "reason":
        reason,
}

Path(
    "spy_sentinel_agent_v96_audit.json"
).write_text(
    json.dumps(
        audit,
        indent=2,
        default=str,
    )
)

print("\nAUDIT")
print(
    "Saved:"
    " spy_sentinel_agent_v96_audit.json"
)

print("\nSAFETY")
print("NO ORDER SUBMITTED")
print("PAPER EXECUTION: DISABLED")
print("LIVE EXECUTION: DISABLED")

# ==================================================
# V97 — OPTIONS MARKET SIGNAL LAYER
# ==================================================

print("\nV97 OPTIONS MARKET SIGNAL")

calls_v97 = [
    x for x in ranked
    if str(x.get("type", "")).lower() == "call"
]

puts_v97 = [
    x for x in ranked
    if str(x.get("type", "")).lower() == "put"
]

def avg_v97(items, key):
    vals = [
        float(x[key])
        for x in items
        if x.get(key) is not None
    ]
    return sum(vals) / len(vals) if vals else None

call_spread_v97 = avg_v97(
    calls_v97,
    "spread_pct"
)

put_spread_v97 = avg_v97(
    puts_v97,
    "spread_pct"
)

call_delta_v97 = avg_v97(
    calls_v97,
    "delta"
)

put_delta_v97 = avg_v97(
    puts_v97,
    "delta"
)

print("Calls analyzed:", len(calls_v97))
print("Puts analyzed:", len(puts_v97))

print(
    "Average call spread %:",
    round(call_spread_v97 * 100, 2)
    if call_spread_v97 is not None
    else "N/A"
)

print(
    "Average put spread %:",
    round(put_spread_v97 * 100, 2)
    if put_spread_v97 is not None
    else "N/A"
)

print(
    "Average call delta:",
    round(call_delta_v97, 4)
    if call_delta_v97 is not None
    else "N/A"
)

print(
    "Average put delta:",
    round(put_delta_v97, 4)
    if put_delta_v97 is not None
    else "N/A"
)

options_bias_v97 = "NEUTRAL"

if (
    candidate
    and candidate.get("type")
):

    t = str(
        candidate["type"]
    ).lower()

    if t == "call":
        options_bias_v97 = "BULLISH CANDIDATE"

    elif t == "put":
        options_bias_v97 = "BEARISH CANDIDATE"

print(
    "Options candidate bias:",
    options_bias_v97
)

print("\nV97 FINAL GATE")
print(
    "Research edge proven:",
    RESEARCH_EDGE_PROVEN
)
print(
    "Execution enabled:",
    EXECUTION_ENABLED
)

print(
    "FINAL DECISION:",
    "NO TRADE"
)

print(
    "Reason: options telemetry is operational, "
    "but predictive edge still requires validation"
)

print("\nNO ORDER SUBMITTED")
print("PAPER EXECUTION: DISABLED")
print("LIVE EXECUTION: DISABLED")

# ==================================================
# V98 — OPTIONS TELEMETRY LOGGER
# ==================================================

import csv

telemetry_file_v98 = Path(
    "spy_sentinel_options_telemetry_v98.csv"
)

row_v98 = {
    "timestamp_utc":
        datetime.now(
            timezone.utc
        ).isoformat(),

    "spy_price":
        spy_price,

    "candidate_symbol":
        candidate["symbol"]
        if candidate
        else "",

    "candidate_type":
        candidate["type"]
        if candidate
        else "",

    "expiration":
        candidate["expiration"]
        if candidate
        else "",

    "strike":
        candidate["strike"]
        if candidate
        else "",

    "bid":
        candidate["bid"]
        if candidate
        else "",

    "ask":
        candidate["ask"]
        if candidate
        else "",

    "mid":
        candidate["mid"]
        if candidate
        else "",

    "spread_pct":
        candidate["spread_pct"]
        if candidate
        else "",

    "delta":
        candidate["delta"]
        if candidate
        else "",

    "atm_pct":
        candidate["atm_pct"]
        if candidate
        else "",

    "options_bias":
        options_bias_v97,

    "research_edge_proven":
        False,

    "execution_enabled":
        False,

    "decision":
        "NO TRADE",
}

write_header_v98 = (
    not telemetry_file_v98.exists()
)

with telemetry_file_v98.open(
    "a",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=row_v98.keys()
    )

    if write_header_v98:
        writer.writeheader()

    writer.writerow(
        row_v98
    )

print("\nV98 TELEMETRY")
print(
    "Saved:",
    telemetry_file_v98
)

print(
    "Rows:",
    sum(
        1 for _ in open(
            telemetry_file_v98
        )
    ) - 1
)

print("\nNO ORDER SUBMITTED")
print("PAPER EXECUTION: DISABLED")
print("LIVE EXECUTION: DISABLED")

# ==================================================
# V99 — SAFE PAPER ORDER PATH
# ==================================================

from alpaca.trading.requests import LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

print("\nV99 PAPER ORDER PATH")

PAPER_ORDER_ARMED = False

paper_order_preview_v99 = None

if candidate:

    limit_price_v99 = round(
        float(candidate["mid"]),
        2
    )

    estimated_cost_v99 = (
        limit_price_v99 * 100
    )

    buying_power_v99 = float(
        account.buying_power
    )

    cost_pass_v99 = (
        estimated_cost_v99
        <= min(
            buying_power_v99 * 0.01,
            500.00
        )
    )

    paper_order_preview_v99 = {
        "symbol":
            candidate["symbol"],
        "qty":
            1,
        "side":
            "BUY",
        "type":
            "LIMIT",
        "limit_price":
            limit_price_v99,
        "time_in_force":
            "DAY",
        "estimated_cost":
            estimated_cost_v99,
        "cost_gate_pass":
            cost_pass_v99,
    }

    print("\nPAPER ORDER PREVIEW")

    for k, v in (
        paper_order_preview_v99.items()
    ):
        print(k, ":", v)

    order_request_v99 = (
        LimitOrderRequest(
            symbol=candidate["symbol"],
            qty=1,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
            limit_price=limit_price_v99,
            client_order_id=(
                "spy-sentinel-v99-"
                + datetime.now(
                    timezone.utc
                ).strftime(
                    "%Y%m%d%H%M%S"
                )
            ),
        )
    )

else:

    cost_pass_v99 = False
    order_request_v99 = None

# ------------------------------------------
# HARD EXECUTION GATES
# ------------------------------------------

all_execution_gates_v99 = (
    candidate is not None
    and RESEARCH_EDGE_PROVEN
    and EXECUTION_ENABLED
    and PAPER_ORDER_ARMED
    and cost_pass_v99
    and not LIVE_TRADING_ENABLED
)

print("\nEXECUTION GATES")
print(
    "Candidate exists:",
    candidate is not None
)
print(
    "Research edge proven:",
    RESEARCH_EDGE_PROVEN
)
print(
    "Execution enabled:",
    EXECUTION_ENABLED
)
print(
    "Paper order armed:",
    PAPER_ORDER_ARMED
)
print(
    "Cost gate passed:",
    cost_pass_v99
)
print(
    "Live trading disabled:",
    not LIVE_TRADING_ENABLED
)

print(
    "ALL GATES PASS:",
    all_execution_gates_v99
)

# ------------------------------------------
# ORDER SUBMISSION
# ------------------------------------------

if all_execution_gates_v99:

    submitted_v99 = (
        trading.submit_order(
            order_data=
                order_request_v99
        )
    )

    print(
        "PAPER ORDER SUBMITTED:",
        submitted_v99.id
    )

else:

    print(
        "PAPER ORDER NOT SUBMITTED"
    )

print("\nV99 STATUS")
print(
    "Order pathway operational"
)
print(
    "Execution remains hard-locked"
)
print(
    "Live trading remains disabled"
)

# ==================================================
# V100 — HACKATHON DEMO SUMMARY
# ==================================================

print("\n")
print("=" * 58)
print("SPY SENTINEL AI — HACKATHON DEMO")
print("Evidence Before Execution")
print("=" * 58)

print("\n1. ACCOUNT")
print("Environment: ALPACA PAPER")
print("Status:", account.status)
print("Buying power:", account.buying_power)

print("\n2. MARKET")
print(f"SPY: ${spy_price:.2f}")

print("\n3. OPTIONS MARKET")
print("Contracts found:", len(contracts))
print("Contracts ranked:", len(ranked))
print("Eligible contracts:", len(eligible))

print("\n4. BEST CANDIDATE")

if candidate:
    print("Symbol:", candidate["symbol"])
    print("Type:", candidate["type"])
    print("Expiration:", candidate["expiration"])
    print("Strike:", candidate["strike"])
    print(
        "Bid / Ask:",
        candidate["bid"],
        "/",
        candidate["ask"]
    )
    print(
        "Spread %:",
        round(candidate["spread_pct"] * 100, 2)
    )
    print("Delta:", candidate["delta"])
else:
    print("NONE")

print("\n5. STRATEGY / VALIDATION GATE")
print("Research edge proven:", RESEARCH_EDGE_PROVEN)

print("\n6. EXECUTION GATES")
print("Execution enabled:", EXECUTION_ENABLED)
print("Paper order armed:", PAPER_ORDER_ARMED)
print("Live trading enabled:", LIVE_TRADING_ENABLED)
print("All gates pass:", all_execution_gates_v99)

print("\n7. PAPER ORDER PREVIEW")

if paper_order_preview_v99:
    print(
        "Symbol:",
        paper_order_preview_v99["symbol"]
    )
    print(
        "Quantity:",
        paper_order_preview_v99["qty"]
    )
    print(
        "Limit price:",
        paper_order_preview_v99["limit_price"]
    )
    print(
        "Estimated cost:",
        paper_order_preview_v99["estimated_cost"]
    )
    print(
        "Cost gate:",
        paper_order_preview_v99["cost_gate_pass"]
    )
else:
    print("NONE")

print("\n8. FINAL AGENT DECISION")

if all_execution_gates_v99:
    demo_decision_v100 = "PAPER TRADE APPROVED"
else:
    demo_decision_v100 = "NO TRADE"

print(demo_decision_v100)

if not RESEARCH_EDGE_PROVEN:
    print(
        "Reason: predictive edge has not passed "
        "independent validation."
    )

print("\n9. AUDIT / SAFETY")
print("Telemetry logging: ACTIVE")
print("Paper order pathway: OPERATIONAL")
print("Paper order submission: BLOCKED")
print("Live trading: DISABLED")

print("\n" + "=" * 58)
print("SPY SENTINEL AI")
print("A trading agent that can refuse to trade.")
print("=" * 58)
