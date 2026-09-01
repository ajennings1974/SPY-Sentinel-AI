import json
from pathlib import Path
from html import escape

BASE = Path.cwd()

data = json.loads(
    (
        BASE
        / "spy_sentinel_rejection_analytics_v145.json"
    ).read_text()
)

reasons = data["top_rejection_reasons"]

reason_html = ""

for reason, count in reasons:
    reason_html += f"""
    <div class="row">
      <span>{escape(reason)}</span>
      <strong>{count}</strong>
    </div>
    """

cf = data["counterfactual"]

html = f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>SPY Sentinel — Rejection Intelligence</title>
<style>
body {{
    background:#07111f;
    color:#f4f7fb;
    font-family:Arial,sans-serif;
    margin:0;
}}
.wrap {{
    max-width:1100px;
    margin:auto;
    padding:28px;
}}
.grid {{
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:12px;
}}
.card,.panel {{
    background:#101c30;
    border:1px solid #263854;
    border-radius:12px;
    padding:18px;
}}
.panel {{
    margin-top:18px;
}}
.small {{
    color:#9fb0c9;
    font-size:12px;
}}
.value {{
    font-size:28px;
    font-weight:700;
}}
.green {{color:#61e69d}}
.amber {{color:#ffcb6b}}
.red {{color:#ff6975}}
.row {{
    display:flex;
    justify-content:space-between;
    padding:10px 0;
    border-bottom:1px solid #20314c;
}}
</style>
</head>

<body>
<div class="wrap">

<h1>SPY Sentinel — Rejection Intelligence</h1>

<p>
Every NO TRADE becomes a measurable learning episode.
</p>

<div class="grid">

<div class="card">
<div class="small">TRADES TAKEN</div>
<div class="value">{data["trades_taken"]}</div>
</div>

<div class="card">
<div class="small">CANDIDATES REJECTED</div>
<div class="value">{data["candidates_rejected"]}</div>
</div>

<div class="card">
<div class="small">REJECTED + CURRENTLY LOSING</div>
<div class="value green">
{cf["would_currently_be_losing"]}
</div>
</div>

<div class="card">
<div class="small">REJECTED + CURRENTLY PROFITABLE</div>
<div class="value amber">
{cf["would_currently_be_profitable"]}
</div>
</div>

</div>

<div class="panel">
<h2>Top Rejection Reasons</h2>
{reason_html}
</div>

<div class="panel">
<h2>Why This Matters</h2>

<p>
SPY Sentinel does not assume that refusing a trade was correct.
Rejected candidates are shadow-tracked so the system can later
measure whether abstention avoided a loss or missed an opportunity.
</p>

<p>
Those lessons may train a Challenger, but they cannot automatically
change the Champion without independent validation.
</p>

</div>

</div>
</body>
</html>
"""

out = BASE / "spy_sentinel_rejection_dashboard_v146.html"
out.write_text(html)

print("V146 rejection dashboard created")
print("Saved:", out.name)
