import unittest

import pandas as pd

from indusense.fault.data import select_features, target_column


def gold_frame() -> pd.DataFrame:
    return pd.DataFrame({
        "machine_id_std": ["M1", "M1"],
        "window_start": pd.to_datetime(["2026-01-01 00:00", "2026-01-01 01:00"]),
        "window_end": pd.to_datetime(["2026-01-01 01:00", "2026-01-01 02:00"]),
        "split_set": ["train", "train"],
        "feat_a": [1.0, 2.0],
        "feat_b": [0.5, 0.6],
        "label_failure_next_6h": [0, 1],
        "label_failure_next_24h": [1, 0],
        "future_incident_count_24h": [0, 1],
    })


class SelectFeaturesTests(unittest.TestCase):
    def test_excludes_ids_and_all_leakage_columns_for_the_chosen_horizon(self):
        features = select_features(gold_frame(), horizon=24)
        self.assertEqual(sorted(features), ["feat_a", "feat_b"])

    def test_target_column_matches_horizon(self):
        self.assertEqual(target_column(24), "label_failure_next_24h")

    def test_missing_target_column_raises(self):
        with self.assertRaises(ValueError):
            select_features(gold_frame(), horizon=48)

    def test_non_numeric_feature_raises(self):
        gold = gold_frame()
        gold["note"] = ["ok", "ok"]
        with self.assertRaises(ValueError):
            select_features(gold, horizon=24)


if __name__ == "__main__":
    unittest.main()
