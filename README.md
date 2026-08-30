# SPY Sentinel AI

**Evidence Before Execution**

SPY Sentinel AI is an AI-assisted trading research and risk-gating system built for the Alpaca AI Trading Agents Hackathon.

Its purpose is not to force trades.

Its purpose is to test strategies rigorously, reject weak evidence, preserve untouched data, and block execution until a repeatable edge is demonstrated.

## Current System Decision

**NO TRADE**

Current evidence does not justify autonomous execution.

Paper trading and live trading remain locked.

## What SPY Sentinel Tests

SPY Sentinel has evaluated multiple strategy families and modeling approaches, including:

- SPY trend and momentum features
- time-of-day and volatility regimes
- opening range breakout logic
- logistic regression
- nonlinear machine-learning models
- adaptive rolling selection
- cross-market features using QQQ, XLK, and XLF
- multi-market breadth and relative strength
- extreme-dislocation setups
- one-time untouched holdout validation
- rolling walk-forward evaluation

## Validation Philosophy

The project follows a strict research process:

1. Develop only on historical training data
2. Validate chronologically
3. Avoid look-ahead bias and data leakage
4. Use rolling out-of-sample windows
5. Preserve untouched future data
6. Reject strategies that fail statistical or economic gates
7. Keep execution disabled until evidence supports deployment

## Latest Research Status

| Test | Result |
|---|---|
| Historical strategy edge | NOT PROVEN |
| One-time true holdout candidate | FAILED |
| Adaptive rolling selection | FAILED |
| Full-history multi-market model | FAILED |
| Extreme-dislocation family | FAILED |
| Fresh Aug 17–28 validation data | UNTOUCHED |
| Paper trading | LOCKED |
| Live trading | LOCKED |

## Latest Rolling Model Snapshot

- Mean balanced accuracy: **50.32%**
- Mean AUC: **50.32%**
- Positive rolling windows: **6 / 10**
- Result: **FAILED GENERALIZATION GATE**

SPY Sentinel does not treat a weak or inconsistent result as an edge.

## Risk Guardrails

- Data leakage protection: **ACTIVE**
- Fresh-data preservation: **ACTIVE**
- Paper execution: **LOCKED**
- Live execution: **LOCKED**
- No strategy is promoted solely because it performs well on one historical period

## Dashboard

Open:

`spy_sentinel_dashboard.html`

The dashboard summarizes the current research state, validation pipeline, execution gate, and risk controls.

## Data

Primary research data includes:

- SPY 5-minute historical data
- QQQ 5-minute historical data
- XLK 5-minute historical data
- XLF 5-minute historical data

The verified base dataset contains approximately three years of aligned 5-minute market history through August 14, 2026.

Fresh August 17–28 data remains reserved for future shadow-forward validation.

## Core Principle

> A trading system should be allowed to say **NO TRADE**.

SPY Sentinel AI is designed to reject weak strategies rather than manufacture confidence.

Execution remains locked until independent evidence demonstrates a repeatable and economically meaningful edge.

## Technology

- Python
- pandas
- scikit-learn
- Alpaca
- GitHub
- GitHub Copilot
- HTML/CSS dashboard

## Project Status

**Research mode**

No autonomous orders are currently permitted.
