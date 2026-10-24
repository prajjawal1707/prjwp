# numbers.py
from app import logic
df = logic.compare("2026-01-02", "2026-02-01", "09:00")
print(logic.metrics(df))
print("worst hours:", sorted(logic.by_hour(df), key=lambda r: -r["mae"])[:3])
print("by horizon:", [(r["key"], round(r["mae"])) for r in logic.by_horizon(df)])
print("worst days:", sorted(logic.by_day(df), key=lambda r: -r["mae"])[:3])