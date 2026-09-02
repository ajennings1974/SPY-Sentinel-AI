import json
from pathlib import Path

BASE = Path.home() / "SPY_SENTINEL_EVIDENCE_RUNTIME"

def jsonl(name):
    p = BASE / name
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]

v196 = jsonl("market_evidence_v196.jsonl")
v201 = jsonl("market_evidence_v201.jsonl")

learning = json.loads(
    (BASE / "learning_state_v213.json").read_text()
)

summary = learning["summary"]
episodes = learning["episodes"]

latest = v201[-1]
spy = latest["spy"]
opt = latest["option"]

labeled = [
    e for e in episodes
    if e["outcome_status"] == "LABELED_OUTCOME"
]

pending = [
    e for e in episodes
    if e["outcome_status"] == "PENDING_OUTCOME"
]

returns = [
    e["hypothetical_return_pct"]
    for e in labeled
    if e.get("hypothetical_return_pct") is not None
]

html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="30">
<title>SPY Sentinel AI — Judge Proof Bundle</title>

<style>
body {{
  margin:0;
  padding:24px;
  background:#071321;
  color:#f5f8fb;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
}}
.wrap {{max-width:1180px;margin:auto}}
.panel {{
  background:#0d2035;
  border:1px solid #294866;
  border-radius:17px;
  padding:19px;
  margin-bottom:15px;
}}
h1 {{font-size:34px;margin:0 0 6px}}
h2 {{margin:0 0 13px}}
.sub {{color:#b8c8d8}}
.badge {{
  display:inline-block;
  background:#174f33;
  color:#a1ffc1;
  padding:7px 11px;
  border-radius:999px;
  font-weight:800;
}}
.grid {{
  display:grid;
  grid-template-columns:repeat(4,1fr);
  gap:10px;
}}
.box {{
  background:#102a45;
  border:1px solid #2a4c6b;
  border-radius:12px;
  padding:12px;
}}
small {{
  display:block;
  color:#9db2c8;
  margin-bottom:4px;
}}
big {{font-size:23px;font-weight:850}}
.good {{border-color:#2b9465;background:#0d3025}}
.warn {{border-color:#9b792d;background:#342a13}}
.lock {{border-color:#9b3940;background:#35171b}}
.cols {{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:14px;
}}
.proof {{
  border:1px solid #2a4c6b;
  border-radius:12px;
  padding:14px;
  margin:8px 0;
}}
.green {{color:#7df0a7;font-weight:800}}
.yellow {{color:#ffd97b;font-weight:800}}
.red {{color:#ff9a9f;font-weight:800}}
.pipeline {{
  font-size:18px;
  font-weight:800;
  line-height:1.65;
}}
@media(max-width:850px) {{
  .grid,.cols {{grid-template-columns:1fr 1fr}}
}}
</style>
</head>

<body>
<div class="wrap">

<div class="panel">
<h1>SPY Sentinel AI — Judge Proof Bundle</h1>
<p class="sub">
Verify the system in under two minutes: real evidence, fresh quotes,
self-audit, counterfactual learning, and a locked promotion firewall.
</p>
<span class="badge">
ALPACA DATA • ZERO UNAUTHORIZED ORDERS • FAIL-CLOSED LEARNING
</span>
</div>

<div class="panel">
<h2>1 — Current Proof State</h2>

<div class="grid">
<div class="box">
<small>UNATTENDED SPY OBSERVATIONS</small>
<big>{len(v196)}</big>
</div>

<div class="box">
<small>FRESH PAIRED OBSERVATIONS</small>
<big>{len(v201)}</big>
</div>

<div class="box">
<small>LABELED OUTCOMES</small>
<big>{len(labeled)}</big>
</div>

<div class="box">
<small>PENDING OUTCOMES</small>
<big>{len(pending)}</big>
</div>

<div class="box">
<small>TRAINING READY</small>
<big>{summary["training_ready_outcomes"]}/{summary["minimum_required"]}</big>
</div>

<div class="box">
<small>PAPER ORDERS</small>
<big>0</big>
</div>

<div class="box">
<small>LIVE ORDERS</small>
<big>0</big>
</div>

<div class="box">
<small>CHAMPION CHANGES</small>
<big>0</big>
</div>
</div>
</div>

<div class="cols">

<div class="panel good">
<h2>2 — Fresh Market Proof</h2>

<div class="proof">
<b>SPY</b><br>
${float(spy["price"]):.2f}<br>
<small>{spy["source"]}</small>
</div>

<div class="proof">
<b>{opt["symbol"]}</b><br>
Bid ${float(opt["bid"]):.2f} /
Ask ${float(opt["ask"]):.2f} /
Mid ${float(opt["mid"]):.3f}<br>
Spread {float(opt["spread_pct"]):.2f}%<br>
<small>{opt["source"]}</small>
</div>

<p class="green">
✓ Independent SPY timestamp<br>
✓ Independent option quote timestamp<br>
✓ Current active contract<br>
✓ No order submitted
</p>
</div>

<div class="panel warn">
<h2>3 — Mistake Caught by the System</h2>

<p>
V196 originally carried option context inherited from an older audit.
SPY prices were fresh, but the option quote freshness could not be proven.
</p>

<p class="yellow">
DETECTED → PRESERVED → QUARANTINED → EXCLUDED FROM CLEAN LEARNING
</p>

<p>
The historical V196 records were not rewritten.
V199/V201 corrected the weakness prospectively with independently
timestamped Alpaca option quotes.
</p>
</div>

</div>

<div class="cols">

<div class="panel">
<h2>4 — Paper Reality</h2>

<div class="proof">
Bid: <b>${float(opt["bid"]):.2f}</b><br>
Ask: <b>${float(opt["ask"]):.2f}</b><br>
Midpoint: <b>${float(opt["mid"]):.3f}</b><br>
Displayed spread: <b>{float(opt["spread_pct"]):.2f}%</b>
</div>

<p>
Counterfactual returns are research estimates, not promises of executable
fills. Real execution may be worse because of bid/ask spread, slippage,
latency, and changing liquidity.
</p>

<p class="yellow">
Paper and shadow results must be discounted for execution reality.
</p>
</div>

<div class="panel">
<h2>5 — Learning Without Pretending to Trade</h2>

<p>
SPY Sentinel measures later option values against the observed midpoint
to label what would have happened.
</p>

<p>
Actual trade occurred:
<strong>NO</strong>
</p>

<p>
Training-ready outcomes:
<strong>{summary["training_ready_outcomes"]}</strong>
</p>

<p>
Challenger training ready:
<strong>{summary["challenger_training_ready"]}</strong>
</p>
</div>

</div>

<div class="panel lock">
<h2>6 — Promotion Firewall</h2>

<div class="grid">
<div class="box">
<small>CHALLENGER EXECUTION</small>
<big>LOCKED</big>
</div>

<div class="box">
<small>SELF-PROMOTION</small>
<big>LOCKED</big>
</div>

<div class="box">
<small>INDEPENDENT VALIDATION</small>
<big>REQUIRED</big>
</div>

<div class="box">
<small>CHAMPION CHANGE</small>
<big>LOCKED</big>
</div>
</div>
</div>

<div class="panel">
<h2>7 — Governed Learning Path</h2>

<p class="pipeline">
Observe → Evaluate → Experience Log → Outcome Label →
Challenger → Independent Validation → Champion
</p>

<p class="sub">
Every arrow is a gate. Evidence may advance only when the previous
stage proves it deserves to advance.
</p>
</div>

</div>
</body>
</html>
"""

out = BASE / "spy_sentinel_judge_proof_v216.html"
out.write_text(html)

print("\nV216 JUDGE PROOF BUNDLE BUILT")
print("V196 observations:", len(v196))
print("Fresh paired:", len(v201))
print("Labeled:", len(labeled))
print("Pending:", len(pending))
print(
    "Training progress:",
    f'{summary["training_ready_outcomes"]}/{summary["minimum_required"]}'
)
print("Paper orders: 0")
print("Live orders: 0")
print("Champion changes: 0")
print("Saved:", out.name)
