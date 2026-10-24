import pandas as pd
import pytest
from app import logic


def make_fc(rows):
    """rows: (startTime, publishTime, generation), all in UTC."""
    df = pd.DataFrame(rows, columns=["startTime", "publishTime", "generation"])
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True)
    return df


def test_forecast_published_after_cutoff_is_never_selected():
    fc = make_fc([
        ("2026-01-15 12:00", "2026-01-14 08:00", 1000),  # before cutoff -> OK
        ("2026-01-15 12:00", "2026-01-14 09:30", 9999),  # after cutoff  -> ignored
    ])
    out = logic.decision_forecast(fc, "2026-01-15", cutoff="09:00")
    assert len(out) == 1
    assert out.iloc[0]["forecast"] == 1000


def test_latest_forecast_before_cutoff_is_chosen():
    fc = make_fc([
        ("2026-01-15 12:00", "2026-01-13 06:00", 100),
        ("2026-01-15 12:00", "2026-01-14 06:00", 200),
        ("2026-01-15 12:00", "2026-01-14 08:59", 300),
    ])
    out = logic.decision_forecast(fc, "2026-01-15", cutoff="09:00")
    assert out.iloc[0]["forecast"] == 300


def test_forecast_published_exactly_at_cutoff_is_included():
    fc = make_fc([("2026-01-15 12:00", "2026-01-14 09:00", 500)])
    out = logic.decision_forecast(fc, "2026-01-15", cutoff="09:00")
    assert len(out) == 1


def test_only_target_day_rows_returned():
    fc = make_fc([
        ("2026-01-14 23:30", "2026-01-13 08:00", 1),
        ("2026-01-15 00:00", "2026-01-13 08:00", 2),
        ("2026-01-16 00:00", "2026-01-13 08:00", 3),
    ])
    out = logic.decision_forecast(fc, "2026-01-15")
    assert list(out["forecast"]) == [2]


def test_cutoff_respects_london_summer_time():
    # In June, 09:00 London = 08:00 UTC
    fc = make_fc([
        ("2026-06-15 12:00", "2026-06-14 07:30", 111),  # 08:30 London -> OK
        ("2026-06-15 12:00", "2026-06-14 08:30", 222),  # 09:30 London -> ignored
    ])
    out = logic.decision_forecast(fc, "2026-06-15", cutoff="09:00")
    assert out.iloc[0]["forecast"] == 111


def test_metrics_values():
    df = pd.DataFrame({"forecast": [110, 90, 130, 70],
                       "actual":   [100, 100, 100, 100]})
    df["error"] = df["forecast"] - df["actual"]    # 10, -10, 30, -30
    m = logic.metrics(df)
    assert m["n"] == 4
    assert m["mae"] == pytest.approx(20)
    assert m["bias"] == pytest.approx(0)
    assert m["rmse"] == pytest.approx((500) ** 0.5)  # (100+100+900+900)/4 = 500
    assert m["nmae_pct"] == pytest.approx(20)