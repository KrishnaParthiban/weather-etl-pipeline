"""Simple tests that need no internet and no database.
Run:  python -m unittest discover -s tests -t . -v
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock
 
import pandas as pd
import requests
 
import config
from etl import extract
from etl.transform import transform
 
 
def make_raw_response():
    """Fake API answer: good rows, a blank, a bad value, a duplicate, future hours."""
    base = pd.Timestamp.now(tz=config.TIMEZONE).tz_localize(None).floor("h")
    hours = [base - pd.Timedelta(hours=4), base - pd.Timedelta(hours=3),
             base - pd.Timedelta(hours=2), base - pd.Timedelta(hours=1), base,
             base + pd.Timedelta(hours=1), base + pd.Timedelta(hours=2),
             base - pd.Timedelta(hours=4)]                     # duplicate hour
    temps = [30, None, 99, 28, 27, 26, 25, 30.5]
    return {"hourly": {
        "time": [h.strftime("%Y-%m-%dT%H:%M") for h in hours],
        "temperature_2m": temps,
        "relative_humidity_2m": [60] * 8,
        "precipitation": [0.0] * 8,
        "wind_speed_10m": [10.0] * 8,
    }}
 
 
class TransformTests(unittest.TestCase):
    def test_cleans_data_and_counts_rejections(self):
        df, stats = transform("TestCity", make_raw_response())
        self.assertEqual(len(df), 3)                       # 3 good rows remain
        self.assertEqual(stats["future_hours_skipped"], 2)
        self.assertEqual(stats["rows_rejected"], 3)        # blank + 99C + duplicate
        self.assertEqual(df["temperature_c"].iloc[0], 30.5)  # duplicate keeps last
        self.assertTrue(df["observed_at"].is_monotonic_increasing)
 
    def test_missing_hourly_data_raises_error(self):
        with self.assertRaises(ValueError):
            transform("TestCity", {})
 
 
class ExtractTests(unittest.TestCase):
    def setUp(self):
        self.city = config.CITIES[0]
        tmp = tempfile.mkdtemp()
        patches = [mock.patch.object(config, "RAW_DIR", Path(tmp)),
                   mock.patch.object(config, "RETRY_WAIT_SECONDS", 0)]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.tmp = Path(tmp)
 
    def test_success_saves_raw_copy(self):
        fake = mock.Mock()
        fake.json.return_value = {"hourly": {"time": []}}
        fake.raise_for_status.return_value = None
        with mock.patch("requests.get", return_value=fake):
            data = extract.fetch_city_weather(self.city)
        self.assertIn("hourly", data)
        saved = json.loads((self.tmp / "coimbatore_latest.json").read_text())
        self.assertIn("hourly", saved)
 
    def test_retries_then_gives_up(self):
        with mock.patch("requests.get", side_effect=requests.ConnectionError("down")) as get:
            with self.assertRaises(RuntimeError):
                extract.fetch_city_weather(self.city)
        self.assertEqual(get.call_count, config.MAX_RETRIES)
 
 
if __name__ == "__main__":
    unittest.main()

