from datetime import datetime
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

now = datetime.now(ET)

minutes = now.hour * 60 + now.minute

market_open = (
    now.weekday() < 5
    and minutes >= 570
    and minutes < 960
)

# To allow a +60 minute counterfactual before 4 PM,
# no new full-learning episode should start after 3 PM.
full_learning_window = (
    now.weekday() < 5
    and minutes >= 570
    and minutes <= 900
)

print("\nV162 SESSION CLOCK")
print("Eastern time:", now.isoformat())
print("Regular market open:", market_open)
print("Full learning window:", full_learning_window)

if not market_open:
    print("STATUS: MARKET CLOSED")
elif not full_learning_window:
    print("STATUS: TOO LATE FOR NEW +60M LEARNING EPISODE")
else:
    print("STATUS: NEW LEARNING EPISODE ALLOWED")
