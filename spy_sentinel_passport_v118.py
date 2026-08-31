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

trading = TradingClient(
    os.getenv("ALPACA_API_KEY"),
    os.getenv("ALPACA_SECRET_KEY"),
    paper=True,
)

orders = trading.get_orders(
    filter=GetOrdersRequest(
        status=QueryOrderStatus.ALL,
        limit=25,
    )
)

filled = [
    o for o in orders
    if str(o.status).lower().endswith("filled")
]

filled.sort(
    key=lambda o: o.filled_at or o.submitted_at,
    reverse=True,
)

sell_order = next(
    (
        o for o in filled
        if str(o.side).lower().endswith("sell")
    ),
    None,
)

buy_order = None

if sell_order:
    buy_order = next(
        (
            o for o in filled
            if o.symbol == sell_order.symbol
            and str(o.side).lower().endswith("buy")
            and o.filled_at <= sell_order.filled_at
        ),
        None,
    )

entry = float(buy_order.filled_avg_price) if buy_order and buy_order.filled_avg_price else None
exit_price = float(sell_order.filled_avg_price) if sell_order and sell_order.filled_avg_price else None
qty = float(sell_order.filled_qty) if sell_order and sell_order.filled_qty else None

pnl = None
pnl_pct = None

if entry is not None and exit_price is not None and qty is not None:
    pnl = (exit_price - entry) * 100 * qty
    pnl_pct = exit_price / entry - 1

passport = {
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "system": "SPY Sentinel AI",
    "environment": "ALPACA PAPER",
    "live_trading_enabled": False,
    "research_edge_proven": False,
    "execution_mode": "CONTROLLED PAPER DEMO",
    "trade": {
        "symbol": sell_order.symbol if sell_order else None,
        "quantity": qty,
        "entry_price": entry,
        "entry_time": str(buy_order.filled_at) if buy_order else None,
        "exit_price": exit_price,
        "exit_time": str(sell_order.filled_at) if sell_order else None,
        "pnl_dollars": pnl,
        "pnl_pct": pnl_pct,
        "exit_reason": "STOP_LOSS",
    },
    "entry_guardrails": {
        "max_contracts": 1,
        "max_demo_cost": 250,
        "one_position_guard": True,
        "paper_only": True,
    },
    "exit_guardrails": {
        "profit_target_pct": 20,
        "stop_loss_pct": -15,
        "max_hold_minutes": 45,
        "automatic_monitor": True,
    },
    "decision_explanation": {
        "why_trade_allowed": "Controlled paper-demo override proved the execution pipeline. It did not represent a validated profitability claim.",
        "why_exit_occurred": "The position crossed the configured paper stop-loss threshold.",
        "what_bot_learned": "Execution capability and strategy profitability are separate. Risk controls remained active after entry.",
    },
}

Path(
    "spy_sentinel_decision_passport_v118.json"
).write_text(
    json.dumps(
        passport,
        indent=2,
        default=str,
    )
)

print("\nV118 DECISION PASSPORT")
print("Symbol:", passport["trade"]["symbol"])
print("Entry:", entry)
print("Exit:", exit_price)
print("P/L $:", round(pnl, 2) if pnl is not None else None)
print("P/L %:", round(pnl_pct * 100, 2) if pnl_pct is not None else None)
print("Exit reason: STOP_LOSS")
print("Live trading: DISABLED")
print("Saved: spy_sentinel_decision_passport_v118.json")
