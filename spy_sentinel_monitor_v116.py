import os
import json
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import QueryOrderStatus

BASE = Path.cwd()
load_dotenv(BASE / ".env")

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

if not API_KEY or not SECRET_KEY:
    raise RuntimeError("Missing Alpaca credentials")

# ==================================================
# HARD SAFETY SETTINGS
# ==================================================

LIVE_TRADING_ENABLED = False
AUTO_EXIT_ARMED = True

PROFIT_TARGET_PCT = 0.20
STOP_LOSS_PCT = -0.15
MAX_HOLD_MINUTES = 45

trading = TradingClient(
    API_KEY,
    SECRET_KEY,
    paper=True,
)

print("\nSPY SENTINEL V116 — POSITION MONITOR")
print("====================================")
print("Environment: PAPER")
print("Live trading enabled:", LIVE_TRADING_ENABLED)
print("Auto exit armed:", AUTO_EXIT_ARMED)
print("Profit target:", f"{PROFIT_TARGET_PCT*100:.0f}%")
print("Stop loss:", f"{STOP_LOSS_PCT*100:.0f}%")
print("Maximum hold:", MAX_HOLD_MINUTES, "minutes")

positions = trading.get_all_positions()

print("\nOPEN POSITIONS:", len(positions))

audit_rows = []

if not positions:
    print("No paper positions to manage.")
    raise SystemExit(0)

for p in positions:

    symbol = p.symbol
    qty = float(p.qty)
    avg_entry = float(p.avg_entry_price)
    current = float(p.current_price)
    market_value = float(p.market_value)
    unrealized_pl = float(p.unrealized_pl)
    unrealized_plpc = float(p.unrealized_plpc)

    # ----------------------------------------------
    # Find most recent filled BUY order for age
    # ----------------------------------------------

    request = GetOrdersRequest(
        status=QueryOrderStatus.ALL,
        symbols=[symbol],
        limit=50,
    )

    orders = trading.get_orders(
        filter=request
    )

    entry_time = None

    filled_buys = [
        o for o in orders
        if str(o.side).lower().endswith("buy")
        and o.filled_at is not None
    ]

    if filled_buys:
        filled_buys.sort(
            key=lambda o: o.filled_at,
            reverse=True
        )
        entry_time = filled_buys[0].filled_at

    if entry_time is not None:

        if entry_time.tzinfo is None:
            entry_time = entry_time.replace(
                tzinfo=timezone.utc
            )

        age_minutes = (
            datetime.now(timezone.utc)
            - entry_time.astimezone(timezone.utc)
        ).total_seconds() / 60

    else:
        age_minutes = None

    # ----------------------------------------------
    # EXIT LOGIC
    # ----------------------------------------------

    exit_reason = None

    if unrealized_plpc >= PROFIT_TARGET_PCT:
        exit_reason = "PROFIT_TARGET"

    elif unrealized_plpc <= STOP_LOSS_PCT:
        exit_reason = "STOP_LOSS"

    elif (
        age_minutes is not None
        and age_minutes >= MAX_HOLD_MINUTES
    ):
        exit_reason = "TIME_EXIT"

    print("\nPOSITION")
    print("Symbol:", symbol)
    print("Qty:", qty)
    print("Entry:", avg_entry)
    print("Current:", current)
    print("Market value:", market_value)
    print("Unrealized P/L:", unrealized_pl)
    print(
        "P/L %:",
        round(unrealized_plpc * 100, 2)
    )
    print(
        "Age minutes:",
        round(age_minutes, 1)
        if age_minutes is not None
        else "UNKNOWN"
    )

    exit_submitted = False
    close_order_id = None

    if exit_reason:

        print("EXIT TRIGGER:", exit_reason)

        if (
            AUTO_EXIT_ARMED
            and not LIVE_TRADING_ENABLED
        ):

            close_order = trading.close_position(
                symbol
            )

            close_order_id = str(
                close_order.id
            )

            exit_submitted = True

            print(
                "PAPER EXIT SUBMITTED:",
                close_order_id
            )

        else:

            print(
                "EXIT BLOCKED BY SAFETY GATE"
            )

    else:

        print("EXIT TRIGGER: NONE")
        print("POSITION REMAINS OPEN")

    audit_rows.append({
        "timestamp_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),
        "symbol":
            symbol,
        "qty":
            qty,
        "entry_price":
            avg_entry,
        "current_price":
            current,
        "market_value":
            market_value,
        "unrealized_pl":
            unrealized_pl,
        "unrealized_pl_pct":
            unrealized_plpc,
        "age_minutes":
            age_minutes,
        "exit_reason":
            exit_reason,
        "exit_submitted":
            exit_submitted,
        "close_order_id":
            close_order_id,
        "paper_environment":
            True,
        "live_trading_enabled":
            False,
    })

Path(
    "spy_sentinel_monitor_v116_audit.json"
).write_text(
    json.dumps(
        audit_rows,
        indent=2,
        default=str
    )
)

print("\nAUDIT")
print(
    "Saved: spy_sentinel_monitor_v116_audit.json"
)

print("\nSAFETY")
print("PAPER ACCOUNT ONLY")
print("LIVE TRADING: DISABLED")
print("NO NEW ENTRY ORDER CODE")
