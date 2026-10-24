import pandas as pd
from app import logic

act, fc = logic.load()
df = logic.compare(logic.MIN_DAY, logic.MAX_DAY)

print("Forecast target minutes:", fc.startTime.dt.minute.value_counts().to_dict())
print("Actual target minutes:  ", act.startTime.dt.minute.value_counts().to_dict())
print("Distinct publish times: ", fc.publishTime.nunique())

days = logic.by_day(df)
bad = [(r["key"], r["n"]) for r in days if r["n"] != 48]
print("Days with n != 48:", bad)

if bad:
    d = bad[0][0]
    exp = pd.date_range(f"{d} 00:00", periods=48, freq="30min", tz=logic.LONDON).tz_convert("UTC")
    have = set(df[df.startTime.dt.tz_convert(logic.LONDON).dt.strftime("%Y-%m-%d") == d].startTime)
    print(f"Missing half-hours on {d}:", [t.strftime("%H:%M") for t in exp if t not in have])