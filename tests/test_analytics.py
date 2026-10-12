"""Unit tests for ABC-XYZ Inventory Analytics Dashboard pipeline."""
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

from data_cleaning import load_data, clean_data, MONTHS, REQUIRED
from category_performance import compute_category_summary, compute_monthly_trend, get_top_products
from abc_xyz_analysis import classify_abc_xyz, compute_matrix, generate_action_recommendations


class TestInventoryAnalytics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw, cls.source = load_data()
        cls.clean, cls.audit = clean_data(cls.raw)
        cls.classified = classify_abc_xyz(cls.clean, a_cutoff=0.80, b_cutoff=0.95, x_cutoff=0.50, y_cutoff=1.00)

    def test_dataset_loaded(self):
        """Test dataset loads and contains required rows."""
        self.assertGreater(len(self.raw), 0)
        self.assertTrue(self.source.endswith(".csv"))

    def test_clean_data_columns_and_reconciliation(self):
        """Test cleaning pipeline guarantees integrity and mathematical consistency."""
        for col in REQUIRED:
            self.assertIn(col, self.clean.columns)

        # Total annual units must equal sum of 12 months
        monthly_sum = self.clean[MONTHS].sum(axis=1)
        np.testing.assert_allclose(self.clean["Total_Annual_Units"], monthly_sum, rtol=1e-5)

        # Total sales value must equal units * price
        expected_sales = self.clean["Total_Annual_Units"] * self.clean["Price_Per_Unit"]
        np.testing.assert_allclose(self.clean["Total_Sales_Value"], expected_sales, rtol=1e-5)

        # No nulls in primary identifiers
        self.assertEqual(int(self.clean[["Item_ID", "Item_Name", "Category"]].isna().sum().sum()), 0)

    def test_category_summary(self):
        """Test category-level summary metrics aggregation."""
        summary = compute_category_summary(self.clean)
        self.assertGreater(len(summary), 0)
        self.assertIn("Category", summary.columns)
        self.assertIn("Sales_Share_%", summary.columns)

        # Shares must sum to approximately 100%
        self.assertAlmostEqual(summary["Sales_Share_%"].sum(), 100.0, places=2)

        # Monthly trend shape
        trend = compute_monthly_trend(self.clean)
        self.assertEqual(len(trend), 12)

        # Top products
        top10 = get_top_products(self.clean, n=10)
        self.assertEqual(len(top10), min(10, len(self.clean)))

    def test_classify_abc_xyz(self):
        """Test ABC and XYZ segmentation rules and classes."""
        self.assertIn("ABC_Class", self.classified.columns)
        self.assertIn("XYZ_Class", self.classified.columns)
        self.assertIn("ABC_XYZ_Class", self.classified.columns)

        # Valid ABC categories
        valid_abc = {"A", "B", "C"}
        self.assertTrue(set(self.classified["ABC_Class"].unique()).issubset(valid_abc))

        # Valid XYZ categories
        valid_xyz = {"X", "Y", "Z", "N/A"}
        self.assertTrue(set(self.classified["XYZ_Class"].unique()).issubset(valid_xyz))

        # Class counts
        self.assertGreater((self.classified["ABC_Class"] == "A").sum(), 0)
        self.assertGreater((self.classified["XYZ_Class"] == "X").sum(), 0)

    def test_matrix_and_recommendations(self):
        """Test 3x3 matrix computation and action recommendations mapping."""
        matrix = compute_matrix(self.classified)
        self.assertEqual(list(matrix.index), ["A", "B", "C"])
        self.assertEqual(list(matrix.columns), ["X", "Y", "Z"])

        rec = generate_action_recommendations(self.classified)
        self.assertEqual(len(rec), len(self.classified))
        self.assertIn("Suggested_Action", rec.columns)
        self.assertEqual(int(rec["Suggested_Action"].isna().sum()), 0)


if __name__ == "__main__":
    unittest.main()
