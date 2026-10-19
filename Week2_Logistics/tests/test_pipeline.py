import unittest
from pathlib import Path
import sys
import pandas as pd
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from preprocessing import clean_data, normalize_data, summarize_orders, load_data, ROOT


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = load_data(ROOT / 'data/raw/DataCoSupplyChainDataset.csv').head(100)

    def test_clean_preserves_rows_and_removes_empty_and_private(self):
        clean, audit, _, _ = clean_data(self.raw)
        self.assertEqual(len(clean), len(self.raw))
        self.assertNotIn('Product Description', clean)
        self.assertNotIn('Customer Password', clean)
        self.assertEqual(audit['missing_after'], 0)

    def test_postal_string_and_unknown_indicator(self):
        raw = self.raw.copy()
        raw.loc[0, 'Customer Zipcode'] = '00725'
        raw.loc[1, 'Customer Zipcode'] = pd.NA
        clean, _, _, _ = clean_data(raw)
        self.assertEqual(clean.loc[0, 'Customer Zipcode'], '00725')
        self.assertEqual(clean.loc[1, 'Customer Zipcode'], 'Unknown')
        self.assertEqual(clean.loc[1, 'Customer Zipcode_missing'], 1)

    def test_extreme_sales_flagged_not_removed(self):
        raw = self.raw.copy()
        raw.loc[0, 'Sales'] = 100000
        clean, _, _, _ = clean_data(raw)
        self.assertEqual(clean.loc[0, 'Sales_iqr_flag'], 1)
        self.assertEqual(clean.loc[0, 'Sales'], 100000)
        self.assertEqual(len(clean), len(raw))

    def test_scaling_preserves_units_and_bounds(self):
        clean, _, _, _ = clean_data(self.raw)
        normalized, _ = normalize_data(clean)
        pd.testing.assert_series_equal(clean['Sales'], normalized['Sales'])
        self.assertTrue(np.isclose(normalized['Sales_minmax'].min(), 0))
        self.assertTrue(np.isclose(normalized['Sales_minmax'].max(), 1))

    def test_constant_feature_scaling(self):
        clean, _, _, _ = clean_data(self.raw)
        clean['Sales'] = 100.
        normalized, _ = normalize_data(clean)
        self.assertTrue((normalized['Sales_minmax'] == 0).all())

    def test_exact_duplicate_removed(self):
        raw = pd.concat([self.raw, self.raw.iloc[[0]]], ignore_index=True)
        clean, audit, _, _ = clean_data(raw)
        self.assertEqual(audit['exact_duplicates_removed'], 1)
        self.assertEqual(len(clean), len(self.raw))

    def test_conflicting_item_key_rejected(self):
        raw = self.raw.copy()
        raw.loc[1, 'Order Item Id'] = raw.loc[0, 'Order Item Id']
        with self.assertRaisesRegex(ValueError, 'Conflicting duplicate'):
            clean_data(raw)

    def test_invalid_date_rejected(self):
        raw = self.raw.copy()
        raw.loc[0, 'order date (DateOrders)'] = 'not a date'
        with self.assertRaisesRegex(ValueError, 'Invalid or missing date'):
            clean_data(raw)

    def test_negative_measurement_rejected(self):
        raw = self.raw.copy()
        raw.loc[0, 'Sales'] = -1
        with self.assertRaisesRegex(ValueError, 'Invalid negative'):
            clean_data(raw)

    def test_missing_schema_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Missing required columns'):
            clean_data(self.raw.drop(columns=['Sales']))

    def test_missing_numeric_not_silently_imputed(self):
        raw = self.raw.copy()
        raw.loc[0, 'Sales'] = np.nan
        with self.assertRaisesRegex(ValueError, 'Missing or non-finite'):
            clean_data(raw)

    def test_unique_order_denominator(self):
        clean, _, _, _ = clean_data(self.raw)
        orders, metrics = summarize_orders(clean)
        self.assertEqual(len(orders), clean['Order Id'].nunique())
        self.assertEqual(metrics['non_canceled_orders'],
                         (orders['Delivery Status'] != 'Shipping canceled').sum())


if __name__ == '__main__':
    unittest.main()
