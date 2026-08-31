import os
import json
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest

BASE = Path.cwd()
load_dotenv(BASE / ".env")

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

trading = TradingClient(
    API_KEY,
    SECRET_KEY,
    paper=True,
)

data = StockHistoricalDataClient(
    API_KEY,
    SECRET_KEY,
)

latest = data.get_stock_latest_trade(
    StockLatestTradeRequest(
        symbol_or_symbols="SPY"
    )
)

spy_price = float(
    latest["SPY"].price
)

audit_file = BASE / "spy_sentinel_agent_v96_audit.json"

candidate = None

if audit_file.exists():
    audit = json.loads(
        audit_file.read_text()
    )
    candidate = audit.get("candidate")

positions = trading.get_all_positions()

account_clear = len(positions) == 0

if candidate:
    mid = float(candidate["mid"])
    estimated_cost = mid * 100
    spread_pct = float(candidate["spread_pct"])
    delta = candidate.get("delta")

    liquidity_pass = bool(
        candidate.get("liquidity_pass")
    )

    atm_pass = bool(
        candidate.get("atm_pass")
    )

    cost_pass = estimated_cost <= 250

else:
    estimated_cost = None
    spread_pct = None
    delta = None
    liquidity_pass = False
    atm_pass = False
    cost_pass = False

gates = {
    "candidate_exists":
        candidate is not None,

    "liquidity_pass":
        liquidity_pass,

    "atm_pass":
        atm_pass,

    "cost_pass":
        cost_pass,

    "account_clear":
        account_clear,

    "validated_edge":
        False,

    "live_authorized":
        False,
}

paper_demo_score = sum([
    gates["candidate_exists"],
    gates["liquidity_pass"],
    gates["atm_pass"],
    gates["cost_pass"],
    gates["account_clear"],
])

paper_demo_total = 5

validated_score = paper_demo_score + int(
    gates["validated_edge"]
)

validated_total = 6

state = {
    "generated_utc":
        datetime.now(
            timezone.utc
        ).isoformat(),

    "spy_price":
        spy_price,

    "candidate":
        candidate,

    "estimated_cost":
        estimated_cost,

    "spread_pct":
        spread_pct,

    "delta":
        delta,

    "gates":
        gates,

    "paper_demo_readiness": {
        "score":
            paper_demo_score,

        "total":
            paper_demo_total,

        "eligible":
            paper_demo_score
            == paper_demo_total,
    },

    "validated_strategy_readiness": {
        "score":
            validated_score,

        "total":
            validated_total,

        "eligible":
            validated_score
            == validated_total,
    },

    "live_money_ready":
        False,
}

Path(
    "spy_sentinel_candidate_v125.json"
).write_text(
    json.dumps(
        state,
        indent=2,
        default=str
    )
)

print("\nV125 LIVE CANDIDATE INTELLIGENCE")
print("SPY price:", spy_price)

if candidate:
    print("Candidate:", candidate["symbol"])
    print("Type:", candidate["type"])
    print("Bid:", candidate["bid"])
    print("Ask:", candidate["ask"])
    print("Delta:", candidate.get("delta"))
    print("Estimated cost:", estimated_cost)
else:
    print("Candidate: NONE")

print(
    "Paper-demo readiness:",
    f"{paper_demo_score}/{paper_demo_total}"
)

print(
    "Validated-strategy readiness:",
    f"{validated_score}/{validated_total}"
)

print("Live-money ready: False")
