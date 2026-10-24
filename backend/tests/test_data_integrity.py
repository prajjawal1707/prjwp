import pandas as pd
import pytest
from app import logic

pytestmark = pytest.mark.skipif(
    not (logic.DATA / "forecasts.csv").exists(), reason="run python -m app.ingest first")


def test_every_day_has_24_hourly_points():
    # WINDFOR is hourly; actuals are half-hourly, so the join gives 24 points/day
    df = logic.compare(logic.MIN_DAY, logic.MAX_DAY)
    per_day = logic.by_day(df)
    assert len(per_day) == 31
    assert all(r["n"] == logic.POINTS_PER_DAY for r in per_day)


def test_forecast_is_hourly():
    _, fc = logic.load()
    assert (fc.startTime.dt.minute == 0).all()


def test_no_forecast_published_after_cutoff():
    df = logic.compare(logic.MIN_DAY, logic.MAX_DAY, "09:00")
    day = df["startTime"].dt.tz_convert(logic.LONDON).dt.strftime("%Y-%m-%d")
    cutoffs = day.map(lambda d: logic._cutoff_ts(d, "09:00"))
    assert (df["publishTime"] <= cutoffs).all()


def test_horizon_is_positive_and_under_two_days():
    df = logic.compare(logic.MIN_DAY, logic.MAX_DAY)
    assert df["horizon_h"].min() > 0
    assert df["horizon_h"].max() < 72


def test_empty_range_is_safe():
    assert logic.metrics(logic.compare("2025-01-01", "2025-01-02"))["n"] == 0