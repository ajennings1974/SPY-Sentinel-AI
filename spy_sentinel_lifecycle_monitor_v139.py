import os
import sys
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest

BASE = Path.cwd()
load_dotenv(BASE / ".env")

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

if not API_KEY or not SECRET_KEY:
    raise RuntimeError("Missing Alpaca API credentials")

# ==================================================
# HARD SAFETY
# ==================================================

PAPER_ONLY = True
LIVE_TRADING_ENABLED = False
DRY_RUN = True

PROFIT_TARGET_PCT = 0.20
STOP_LOSS_PCT = -0.15
MAX_HOLD_MINUTES = 45

STATE_FILE = BASE / "spy_sentinel_lifecycle_state_v139.json"
EVENT_FILE = BASE / "spy_sentinel_lifecycle_events_v139.jsonl"

trading = TradingClient(
    API_KEY,
    SECRET_KEY,
    paper=True,
)

stock_data = StockHistoricalDataClient(
    API_KEY,
    SECRET_KEY,
)

def now_utc():
    return datetime.now(timezone.utc)

def save_state(state):
    STATE_FILE.write_text(
        json.dumps(
            state,
            indent=2,
            default=str,
        )
    )

def append_event(event):
    with EVENT_FILE.open("a") as f:
        f.write(
            json.dumps(
                event,
                default=str,
            )
            + "\n"
        )

def get_spy_price():
    try:
        latest = stock_data.get_stock_latest_trade(
            StockLatestTradeRequest(
                symbol_or_symbols="SPY"
            )
        )
        return float(latest["SPY"].price)
    except Exception:
        return None

def new_decision_id():
    return "spy-" + uuid.uuid4().hex[:12]

def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(
                STATE_FILE.read_text()
            )
        except Exception:
            pass
    return None

def determine_exit(pl_pct, holding_minutes):
    if pl_pct >= PROFIT_TARGET_PCT:
        return "PROFIT_TARGET"

    if pl_pct <= STOP_LOSS_PCT:
        return "STOP_LOSS"

    if holding_minutes >= MAX_HOLD_MINUTES:
        return "TIME_EXIT"

    return None

def update_episode(
    symbol,
    qty,
    entry_price,
    current_price,
    pl_pct,
    holding_minutes,
    spy_price,
    simulation=False,
):
    state = load_state()

    if (
        state is None
        or state.get("status") == "CLOSED"
        or state.get("symbol") != symbol
    ):
        state = {
            "decision_id": new_decision_id(),
            "status": "OPEN",
            "symbol": symbol,
            "qty": qty,
            "entry_price": entry_price,
            "first_seen_utc": now_utc().isoformat(),
            "mfe_pct": pl_pct,
            "mae_pct": pl_pct,
            "exit_pending": False,
            "exit_reason": None,
            "exit_order_id": None,
            "monitor_ticks": 0,
        }

        append_event({
            "decision_id": state["decision_id"],
            "event": "POSITION_DISCOVERED",
            "timestamp_utc": now_utc().isoformat(),
            "symbol": symbol,
            "qty": qty,
            "entry_price": entry_price,
            "spy_price": spy_price,
            "simulation": simulation,
        })

    state["monitor_ticks"] += 1
    state["current_price"] = current_price
    state["current_pl_pct"] = pl_pct
    state["holding_minutes"] = holding_minutes
    state["spy_price_latest"] = spy_price

    state["mfe_pct"] = max(
        float(state.get("mfe_pct", pl_pct)),
        pl_pct,
    )

    state["mae_pct"] = min(
        float(state.get("mae_pct", pl_pct)),
        pl_pct,
    )

    exit_reason = determine_exit(
        pl_pct,
        holding_minutes,
    )

    append_event({
        "decision_id": state["decision_id"],
        "event": "MONITOR_TICK",
        "timestamp_utc": now_utc().isoformat(),
        "symbol": symbol,
        "option_price": current_price,
        "spy_price": spy_price,
        "pl_pct": pl_pct,
        "holding_minutes": holding_minutes,
        "mfe_pct": state["mfe_pct"],
        "mae_pct": state["mae_pct"],
        "exit_trigger": exit_reason,
        "simulation": simulation,
    })

    if exit_reason:
        state["exit_reason"] = exit_reason

        if state.get("exit_pending"):
            append_event({
                "decision_id": state["decision_id"],
                "event": "DUPLICATE_EXIT_BLOCKED",
                "timestamp_utc": now_utc().isoformat(),
                "reason": exit_reason,
            })

            print("Duplicate exit blocked")

        else:
            state["exit_pending"] = True

            append_event({
                "decision_id": state["decision_id"],
                "event": "EXIT_PROPOSED",
                "timestamp_utc": now_utc().isoformat(),
                "reason": exit_reason,
                "dry_run": DRY_RUN,
            })

            if DRY_RUN:
                print(
                    "DRY RUN — EXIT WOULD TRIGGER:",
                    exit_reason
                )

            else:
                raise RuntimeError(
                    "V139 is not authorized for order submission"
                )

    save_state(state)

    print("\nV139 LIFECYCLE STATE")
    print("Decision ID:", state["decision_id"])
    print("Symbol:", symbol)
    print("Current P/L %:", round(pl_pct * 100, 2))
    print("MFE %:", round(state["mfe_pct"] * 100, 2))
    print("MAE %:", round(state["mae_pct"] * 100, 2))
    print("Holding minutes:", round(holding_minutes, 2))
    print("Exit trigger:", exit_reason)
    print("Exit pending:", state["exit_pending"])

    return state

def run_real():
    positions = trading.get_all_positions()

    print("\nSPY SENTINEL V139 — REAL PAPER MONITOR")
    print("Open positions:", len(positions))

    if not positions:
        print("No paper position to monitor")
        return

    for p in positions:
        symbol = p.symbol
        qty = float(p.qty)
        entry = float(p.avg_entry_price)
        current = float(p.current_price)
        pl_pct = float(p.unrealized_plpc)

        holding_minutes = 0.0

        existing = load_state()

        if (
            existing
            and existing.get("symbol") == symbol
            and existing.get("first_seen_utc")
        ):
            try:
                first_seen = datetime.fromisoformat(
                    existing["first_seen_utc"]
                )

                holding_minutes = (
                    now_utc()
                    - first_seen
                ).total_seconds() / 60

            except Exception:
                pass

        update_episode(
            symbol=symbol,
            qty=qty,
            entry_price=entry,
            current_price=current,
            pl_pct=pl_pct,
            holding_minutes=holding_minutes,
            spy_price=get_spy_price(),
            simulation=False,
        )

def run_simulation():
    print("\nSPY SENTINEL V139 — SIMULATION")
    print("NO ALPACA ORDER WILL BE SENT")

    if STATE_FILE.exists():
        STATE_FILE.unlink()

    simulated = [
        (0.05, 5),
        (0.12, 12),
        (-0.03, 20),
        (-0.18, 30),
        (-0.20, 31),
    ]

    symbol = "SIM_SPY_OPTION"

    for pl_pct, minutes in simulated:
        current_price = 1.00 * (1 + pl_pct)

        update_episode(
            symbol=symbol,
            qty=1,
            entry_price=1.00,
            current_price=current_price,
            pl_pct=pl_pct,
            holding_minutes=minutes,
            spy_price=500.00,
            simulation=True,
        )

    print("\nSIMULATION COMPLETE")
    print("Expected MFE: +12%")
    print("Expected MAE: -20%")
    print("Expected exit trigger: STOP_LOSS")
    print("Expected duplicate exit protection: ACTIVE")

if "--simulate" in sys.argv:
    run_simulation()
else:
    run_real()

print("\nSAFETY")
print("PAPER ONLY:", PAPER_ONLY)
print("LIVE TRADING:", LIVE_TRADING_ENABLED)
print("DRY RUN:", DRY_RUN)
print("NO ORDER SUBMISSION CODE")
