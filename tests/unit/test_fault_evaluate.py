import unittest

import numpy as np
import pandas as pd

from indusense.fault.evaluate import arbitration_table, choose_threshold, evaluate_at_threshold


class ChooseThresholdTests(unittest.TestCase):
    def test_threshold_separates_perfectly_separable_scores(self):
        y_true = pd.Series([0, 0, 0, 1, 1, 1])
        scores = np.array([0.1, 0.2, 0.3, 0.7, 0.8, 0.9])
        threshold = choose_threshold(y_true, scores)
        predicted = (scores >= threshold).astype(int)
        self.assertListEqual(predicted.tolist(), y_true.tolist())


class EvaluateAtThresholdTests(unittest.TestCase):
    def test_confusion_counts_match_known_case(self):
        y_true = pd.Series([0, 0, 1, 1])
        scores = np.array([0.1, 0.6, 0.4, 0.9])
        metrics = evaluate_at_threshold(y_true, scores, threshold=0.5)
        self.assertEqual((metrics.TN, metrics.FP, metrics.FN, metrics.TP), (1, 1, 1, 1))
        self.assertAlmostEqual(metrics.precision, 0.5)
        self.assertAlmostEqual(metrics.recall, 0.5)


class ArbitrationTableTests(unittest.TestCase):
    def test_builds_dataframe_with_expected_columns(self):
        rows = [
            {"modele": "reference", "pr_auc": 0.42, "gco2eq": 1.2, "interpretabilite": "haute",
             "decision": "retenu"},
        ]
        table = arbitration_table(rows)
        self.assertEqual(list(table.columns), ["modele", "pr_auc", "gco2eq", "interpretabilite", "decision"])
        self.assertEqual(len(table), 1)

    def test_missing_column_raises(self):
        with self.assertRaises(ValueError):
            arbitration_table([{"modele": "reference"}])


if __name__ == "__main__":
    unittest.main()
