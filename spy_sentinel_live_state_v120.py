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

positions = trading.get_all_positions()

orders = trading.get_orders(
    filter=GetOrdersRequest(
        status=QueryOrderStatus.ALL,
        limit=20,
    )
)

latest_order = orders[0] if orders else None

state = {
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "system": "SPY Sentinel AI",
    "environment": "ALPACA PAPER",
    "live_trading_enabled": False,
    "active_paper_agent": True,

    "open_positions": len(positions),

    "latest_order": {
        "symbol": latest_order.symbol if latest_order else None,
        "side": str(latest_order.side) if latest_order else None,
        "status": str(latest_order.status) if latest_order else None,
        "filled_qty": str(latest_order.filled_qty) if latest_order else None,
        "filled_avg_price": str(latest_order.filled_avg_price) if latest_order else None,
        "filled_at": str(latest_order.filled_at) if latest_order else None,
    },

    "risk_controls": {
        "paper_only": True,
        "max_contracts": 1,
        "max_demo_cost": 250,
        "profit_target_pct": 20,
        "stop_loss_pct": -15,
        "max_hold_minutes": 45,
        "automatic_monitor": True,
    },

    "current_decision": {
        "action": "NO TRADE" if len(positions) == 0 else "MANAGE POSITION",
        "reason": (
            "No open paper position. Awaiting a candidate that passes demo gates."
            if len(positions) == 0
            else
            "Existing paper position is being monitored by risk controls."
        )
    },

    "why_not_trade": [
        {
            "gate": "Validated profitability edge",
            "status": "NOT PROVEN",
            "meaning": "Execution capability exists, but the research does not justify a profitability claim."
        },
        {
            "gate": "Live-money authorization",
            "status": "DISABLED",
            "meaning": "SPY Sentinel cannot submit live-money orders."
        },
        {
            "gate": "One-position rule",
            "status": "ACTIVE",
            "meaning": "The agent will not stack uncontrolled demo positions."
        },
    ]
}

Path(
    "spy_sentinel_live_state_v120.json"
).write_text(
    json.dumps(
        state,
        indent=2,
        default=str
    )
)

print("V120 live state generated")
print("Open positions:", len(positions))
print("Decision:", state["current_decision"]["action"])
print("Live trading: DISABLED")
