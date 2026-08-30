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
