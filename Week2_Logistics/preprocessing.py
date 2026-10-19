"""Week 2: reproducible DataCo cleaning, auditing and descriptive scaling.
Run: python preprocessing.py
Original values are retained. Full-data scaling is NOT a model-training step.
"""
from pathlib import Path
import argparse
import hashlib
import json
import platform
import numpy as np
import pandas as pd
import sklearn
from sklearn.preprocessing import MinMaxScaler

ROOT = Path(__file__).resolve().parent
DATES = ['order date (DateOrders)', 'shipping date (DateOrders)']
CORE = ['Sales', 'Order Item Quantity', 'Days for shipping (real)',
        'Days for shipment (scheduled)']
IQR_COLS = ['Sales', 'Order Item Quantity', 'Order Item Discount',
            'Order Item Profit Ratio', 'Days for shipping (real)']
SCALE = ['Sales', 'Order Item Quantity', 'Days for shipping (real)']
PRIVATE = ['Customer Email', 'Customer Password', 'Customer Fname',
           'Customer Lname', 'Customer Street', 'Product Image']
ORDER_FIELDS = ['Days for shipping (real)', 'Days for shipment (scheduled)',
                'Late_delivery_risk', 'Delivery Status', 'Shipping Mode',
                'Order Status']
REQUIRED = list(dict.fromkeys(CORE + IQR_COLS + DATES + ORDER_FIELDS +
                             ['Order Id', 'Order Item Id', 'Customer Zipcode',
                              'Order Zipcode']))


def load_data(path):
    # String dtype preserves source tokens (never infer postal codes as integers).
    return pd.read_csv(path, encoding='latin1', low_memory=False,
                       dtype={'Customer Zipcode': 'string',
                              'Order Zipcode': 'string'})


def clean_data(raw):
    missing = sorted(set(REQUIRED) - set(raw.columns))
    if missing:
        raise ValueError(f'Missing required columns: {missing}')
    if raw.empty:
        raise ValueError('Dataset is empty')
    df = raw.copy()
    before = df.isna().sum()
    audit = {'raw_rows': len(df), 'raw_columns': len(df.columns),
             'missing_before': {k: int(v) for k, v in before.items() if v},
             'exact_duplicates_removed': int(df.duplicated().sum())}
    df = df.drop_duplicates().copy()
    for col in df.select_dtypes(include=['object', 'string']).columns:
        df[col] = df[col].astype('string').str.strip().replace('', pd.NA)
    if df[['Order Id', 'Order Item Id']].isna().any().any():
        raise ValueError('Missing order or item identifiers')
    if df['Order Item Id'].duplicated().any():
        raise ValueError('Conflicting duplicate Order Item Id: investigate source')
    empty = df.columns[df.isna().all()].tolist()
    if set(empty).intersection(REQUIRED):
        raise ValueError('A required column is completely empty')
    df = df.drop(columns=empty)
    audit['empty_columns_removed'] = empty
    removed_private = [c for c in PRIVATE if c in df.columns]
    audit['excluded_personal_or_irrelevant_columns'] = removed_private
    df = df.drop(columns=removed_private)
    for col in ['Customer Zipcode', 'Order Zipcode']:
        df[col + '_missing'] = df[col].isna().astype('int8')
        df[col] = df[col].fillna('Unknown')
    for col in DATES:
        df[col] = pd.to_datetime(df[col], format='%m/%d/%Y %H:%M',
                                 errors='coerce')
        if df[col].isna().any():
            raise ValueError(f'Invalid or missing date in {col}')
    for col in set(CORE + IQR_COLS + ['Late_delivery_risk']):
        df[col] = pd.to_numeric(df[col], errors='coerce')
        if df[col].isna().any() or not np.isfinite(df[col]).all():
            raise ValueError(f'Missing or non-finite numeric value in {col}')
    if (df[CORE] < 0).any().any() or (df['Order Item Quantity'] <= 0).any():
        raise ValueError('Invalid negative core measurement or nonpositive quantity')
    integer_cols = ['Order Item Quantity', 'Days for shipping (real)',
                    'Days for shipment (scheduled)']
    if any((df[c] % 1 != 0).any() for c in integer_cols):
        raise ValueError('Non-integer quantity or shipping-day field')
    if not df['Late_delivery_risk'].isin([0, 1]).all():
        raise ValueError('Late_delivery_risk must be binary')
    if df[ORDER_FIELDS].isna().any().any():
        raise ValueError('Missing order-level field')
    inconsistent = df.groupby('Order Id')[ORDER_FIELDS].nunique().gt(1).any()
    if inconsistent.any():
        raise ValueError('Inconsistent order fields: ' + ', '.join(inconsistent[inconsistent].index))
    elapsed = (df[DATES[1]] - df[DATES[0]]).dt.total_seconds() / 86400
    if (elapsed < 0).any():
        raise ValueError('Shipping timestamp precedes order timestamp')
    df['timestamp_elapsed_days'] = elapsed
    df['timestamp_day_difference_flag'] = (~np.isclose(
        elapsed, df['Days for shipping (real)'], atol=1 / 1440)).astype('int8')
    df['shipping_delay_days'] = (df['Days for shipping (real)'] -
                                 df['Days for shipment (scheduled)'])
    df['is_canceled'] = (df['Delivery Status'] == 'Shipping canceled').astype('int8')
    df['late_rule_mismatch_flag'] = ((df['shipping_delay_days'] > 0).astype(int)
                                    != df['Late_delivery_risk']).astype('int8')
    outliers = []
    for col in IQR_COLS:
        q1, q3 = df[col].quantile([.25, .75])
        low, high = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
        mask = (df[col] < low) | (df[col] > high)
        df[col + '_iqr_flag'] = mask.astype('int8')
        outliers.append({'column': col, 'q1': q1, 'q3': q3,
                         'lower_bound': low, 'upper_bound': high,
                         'flagged_rows': int(mask.sum()),
                         'flagged_pct': float(mask.mean() * 100)})
    audit.update({'clean_rows': len(df), 'clean_columns': len(df.columns),
                  'unique_orders': int(df['Order Id'].nunique()),
                  'missing_after': int(df.isna().sum().sum()),
                  'timestamp_difference_rows': int(df['timestamp_day_difference_flag'].sum()),
                  'late_rule_mismatch_rows': int(df['late_rule_mismatch_flag'].sum()),
                  'late_rule_mismatches_non_canceled': int(df.loc[df['is_canceled'] == 0, 'late_rule_mismatch_flag'].sum())})
    after = df.isna().sum()
    quality = pd.DataFrame({'column': raw.columns,
                            'missing_before': before.values,
                            'missing_after': [int(after[c]) if c in after else None for c in raw.columns],
                            'action': ['excluded' if c not in after else 'retained' for c in raw.columns]})
    return df, audit, pd.DataFrame(outliers), quality


def normalize_data(clean):
    normalized = clean.copy()
    scaler = MinMaxScaler()
    names = [c + '_minmax' for c in SCALE]
    normalized[names] = scaler.fit_transform(clean[SCALE])
    parameters = {'purpose': 'descriptive full-dataset scaling only',
                  'formula': '(x - data_min) / (data_max - data_min)',
                  'features': {c: {'data_min': float(scaler.data_min_[i]),
                                   'data_max': float(scaler.data_max_[i]),
                                   'output': names[i]}
                               for i, c in enumerate(SCALE)}}
    return normalized, parameters


def summarize_orders(clean):
    # Order fields were checked for within-order consistency before deduplication.
    orders = clean[['Order Id'] + ORDER_FIELDS].drop_duplicates('Order Id').copy()
    orders['shipping_delay_days'] = (orders['Days for shipping (real)'] -
                                      orders['Days for shipment (scheduled)'])
    completed = orders[orders['Delivery Status'] != 'Shipping canceled']
    if completed.empty:
        raise ValueError('No non-canceled orders available for shipping KPIs')
    metrics = {'order_item_rows': len(clean), 'unique_orders': len(orders),
               'canceled_orders': len(orders) - len(completed),
               'non_canceled_orders': len(completed),
               'late_non_canceled_orders': int(completed['Late_delivery_risk'].sum()),
               'late_non_canceled_pct': float(completed['Late_delivery_risk'].mean() * 100),
               'mean_actual_shipping_days_non_canceled': float(completed['Days for shipping (real)'].mean()),
               'mean_signed_delay_days_non_canceled': float(completed['shipping_delay_days'].mean()),
               'line_weighted_late_pct_all_statuses': float(clean['Late_delivery_risk'].mean() * 100),
               'sales_min': float(clean['Sales'].min()),
               'sales_max': float(clean['Sales'].max()),
               'sales_mean_per_item': float(clean['Sales'].mean()),
               'shipping_modes_non_canceled': completed.groupby('Shipping Mode').agg(
                   orders=('Order Id', 'size'), late_rate=('Late_delivery_risk', 'mean')).reset_index().to_dict('records')}
    return orders, metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT / 'data/raw/DataCoSupplyChainDataset.csv')
    parser.add_argument('--output', type=Path, default=ROOT / 'results')
    args = parser.parse_args()
    clean, audit, outliers, quality = clean_data(load_data(args.input))
    normalized, params = normalize_data(clean)
    orders, metrics = summarize_orders(clean)
    audit['input_sha256'] = hashlib.sha256(args.input.read_bytes()).hexdigest()
    audit['versions'] = {'python': platform.python_version(), 'pandas': pd.__version__,
                         'numpy': np.__version__, 'scikit_learn': sklearn.__version__}
    args.output.mkdir(parents=True, exist_ok=True)
    clean.to_csv(args.output / 'DataCoSupplyChain_Cleaned.csv', index=False, encoding='utf-8')
    normalized.to_csv(args.output / 'DataCoSupplyChain_Normalized.csv', index=False, encoding='utf-8')
    orders.to_csv(args.output / 'order_summary.csv', index=False)
    outliers.to_csv(args.output / 'outlier_summary.csv', index=False)
    quality.to_csv(args.output / 'missing_values.csv', index=False)
    for name, obj in [('audit_summary', audit), ('scaler_parameters', params),
                      ('analysis_summary', metrics)]:
        (args.output / (name + '.json')).write_text(json.dumps(obj, indent=2), encoding='utf-8')
    print(f'SUCCESS: {len(clean):,} item rows, {len(orders):,} orders. Results: {args.output}')
    print('IQR extremes retained; original units preserved; descriptive scaled columns appended.')


if __name__ == '__main__':
    main()
