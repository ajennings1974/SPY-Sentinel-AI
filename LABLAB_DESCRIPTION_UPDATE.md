SPY Sentinel AI is an Alpaca-connected autonomous paper-trading agent built around evidence-before-execution.

The system analyzes SPY and live options candidates, applies deterministic liquidity, cost, position, and risk gates, and can either execute a tightly controlled Alpaca paper trade or explicitly abstain with a documented NO TRADE reason.

Unlike the original research-only checkpoint, SPY Sentinel now demonstrates a complete closed-loop paper lifecycle:

candidate selection → risk gates → paper entry → fill → automatic position monitoring → deterministic profit-target / stop-loss / time-exit rules → automatic exit → realized outcome → audit trail.

Every completed trade is preserved in a Decision Passport and can be replayed through the dashboard.

SPY Sentinel also records rejected candidates as learning episodes. The architecture is designed to shadow-track rejected setups and later determine whether refusing the trade avoided a loss or missed an opportunity.

Learning is deliberately fail-closed. Bad or stale records are quarantined. A Challenger model may eventually learn from clean accepted and rejected episodes, but it cannot execute, self-promote, or replace the current Champion without independent out-of-sample and fresh-paper validation.

Live-money execution remains disabled.

SPY Sentinel's differentiator is not simply that it can trade. It can explain why it traded, explain why it refused, measure whether those decisions were good, and prevent unvalidated lessons from changing production behavior.
