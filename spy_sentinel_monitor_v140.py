import os
import json
import uuid
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

if not API_KEY or not SECRET_KEY:
    raise RuntimeError("Missing Alpaca credentials")

# ==================================================
# SAFETY
# ==================================================

PAPER_ONLY = True
LIVE_TRADING_ENABLED = False
EXIT_SUBMISSION_ENABLED = False

PROFIT_TARGET_PCT = 0.20
STOP_LOSS_PCT = -0.15
MAX_HOLD_MINUTES = 45

STATE_FILE = BASE / "spy_sentinel_monitor_state_v140.json"
EVENT_FILE = BASE / "spy_sentinel_monitor_events_v140.jsonl"

trading = TradingClient(
    API_KEY,
    SECRET_KEY,
    paper=True,
)

stock_data = StockHistoricalDataClient(
    API_KEY,
    SECRET_KEY,
)

def utcnow():
    return datetime.now(timezone.utc)

def load_state():
    if not STATE_FILE.exists():
        return {}

    try:
        return json.loads(
            STATE_FILE.read_text()
        )
    except Exception:
        return {}

def save_state(state):
    STATE_FILE.write_text(
        json.dumps(
            state,
            indent=2,
            default=str
        )
    )

def append_event(event):
    with EVENT_FILE.open("a") as f:
        f.write(
            json.dumps(
                event,
                default=str
            ) + "\n"
        )

def spy_price():
    try:
        x = stock_data.get_stock_latest_trade(
            StockLatestTradeRequest(
                symbol_or_symbols="SPY"
            )
        )

        return float(
            x["SPY"].price
        )

    except Exception:
        return None

def decision_id():
    return "spy-" + uuid.uuid4().hex[:12]

def exit_trigger(pl_pct, holding_minutes):
    if pl_pct >= PROFIT_TARGET_PCT:
        return "PROFIT_TARGET"

    if pl_pct <= STOP_LOSS_PCT:
        return "STOP_LOSS"

    if holding_minutes >= MAX_HOLD_MINUTES:
        return "TIME_EXIT"

    return None

positions = trading.get_all_positions()

print("\nSPY SENTINEL V140 — INTEGRATED PAPER MONITOR")
print("Open paper positions:", len(positions))

if not positions:
    print("No open paper position.")
    print("Nothing to monitor.")

else:
    state = load_state()

    for p in positions:

        symbol = p.symbol
        qty = float(p.qty)
        entry = float(p.avg_entry_price)
        current = float(p.current_price)
        pl_pct = float(p.unrealized_plpc)

        existing = state.get(symbol)

        if existing is None:
            existing = {
                "decision_id": decision_id(),
                "symbol": symbol,
                "quantity": qty,
                "entry_price": entry,
                "first_seen_utc": utcnow().isoformat(),
                "mfe_pct": pl_pct,
                "mae_pct": pl_pct,
                "monitor_ticks": 0,
                "exit_pending": False,
                "exit_reason": None,
            }

            append_event({
                "decision_id": existing["decision_id"],
                "event": "POSITION_DISCOVERED",
                "timestamp_utc": utcnow().isoformat(),
                "symbol": symbol,
                "entry_price": entry,
                "quantity": qty,
                "spy_price": spy_price(),
            })

        try:
            first_seen = datetime.fromisoformat(
                existing["first_seen_utc"]
            )

            holding_minutes = (
                utcnow() - first_seen
            ).total_seconds() / 60

        except Exception:
            holding_minutes = 0.0

        existing["monitor_ticks"] += 1

        existing["current_price"] = current
        existing["current_pl_pct"] = pl_pct
        existing["holding_minutes"] = holding_minutes
        existing["spy_price_latest"] = spy_price()

        existing["mfe_pct"] = max(
            float(existing["mfe_pct"]),
            pl_pct,
        )

        existing["mae_pct"] = min(
            float(existing["mae_pct"]),
            pl_pct,
        )

        trigger = exit_trigger(
            pl_pct,
            holding_minutes,
        )

        existing["exit_reason"] = trigger

        append_event({
            "decision_id": existing["decision_id"],
            "event": "MONITOR_TICK",
            "timestamp_utc": utcnow().isoformat(),
            "symbol": symbol,
            "option_price": current,
            "spy_price": existing["spy_price_latest"],
            "pl_pct": pl_pct,
            "holding_minutes": holding_minutes,
            "mfe_pct": existing["mfe_pct"],
            "mae_pct": existing["mae_pct"],
            "exit_trigger": trigger,
        })

        if trigger:

            if existing["exit_pending"]:

                append_event({
                    "decision_id": existing["decision_id"],
                    "event": "DUPLICATE_EXIT_BLOCKED",
                    "timestamp_utc": utcnow().isoformat(),
                    "reason": trigger,
                })

                print("Duplicate exit blocked")

            else:

                existing["exit_pending"] = True

                append_event({
                    "decision_id": existing["decision_id"],
                    "event": "EXIT_PROPOSED",
                    "timestamp_utc": utcnow().isoformat(),
                    "reason": trigger,
                    "submission_enabled": EXIT_SUBMISSION_ENABLED,
                })

                print(
                    "EXIT PROPOSED:",
                    trigger
                )

                if not EXIT_SUBMISSION_ENABLED:
                    print(
                        "EXIT SUBMISSION BLOCKED — SAFETY MODE"
                    )

        state[symbol] = existing

        print("\nPOSITION")
        print("Decision ID:", existing["decision_id"])
        print("Symbol:", symbol)
        print("Current P/L %:", round(pl_pct * 100, 2))
        print("MFE %:", round(existing["mfe_pct"] * 100, 2))
        print("MAE %:", round(existing["mae_pct"] * 100, 2))
        print("Holding minutes:", round(holding_minutes, 2))
        print("Exit trigger:", trigger)
        print("Exit pending:", existing["exit_pending"])

    save_state(state)

print("\nSAFETY")
print("PAPER ONLY:", PAPER_ONLY)
print("LIVE TRADING:", LIVE_TRADING_ENABLED)
print("EXIT SUBMISSION ENABLED:", EXIT_SUBMISSION_ENABLED)
