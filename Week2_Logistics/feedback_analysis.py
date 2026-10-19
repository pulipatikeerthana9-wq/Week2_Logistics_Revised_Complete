"""Supplementary feedback evidence; existing cleaning rules remain unchanged.
Run after preprocessing.py: python feedback_analysis.py
No personal field values are exported. Original item-level CSV is preserved.
"""
from pathlib import Path
import json
import pandas as pd

BASE = Path(__file__).resolve().parent


def calculate(df):
    orders = df.drop_duplicates('Order Id')
    completed = orders[orders['Delivery Status'] != 'Shipping canceled']
    lines = df[df['Delivery Status'] != 'Shipping canceled']
    scenarios = []
    for label, frame in [('Item rows, all statuses', df),
                         ('Item rows, non-canceled', lines),
                         ('Unique orders, all statuses', orders),
                         ('Unique orders, non-canceled', completed)]:
        scenarios.append({'population': label, 'records': len(frame),
                          'late_records': int(frame.Late_delivery_risk.sum()),
                          'late_rate_pct': float(frame.Late_delivery_risk.mean()*100)})
    postal = orders.groupby('Market').agg(
        orders=('Order Id', 'size'), unknown=('Order Zipcode_missing', 'sum'))
    postal['known'] = postal.orders - postal.unknown
    postal['known_pct'] = postal.known / postal.orders * 100
    tail = df['Sales_iqr_flag'].astype(bool)
    retained, deleted = df, df.loc[~tail]
    total = float(df.Sales.sum())
    metrics = {
        'scope': 'Calculated from historical DataCo cleaned data; no new cleaning applied',
        'order_volume_inflation_pct': (len(df)/len(orders)-1)*100,
        'known_postal_orders': int((orders.Order_Zipcode_missing == 0).sum()) if 'Order_Zipcode_missing' in orders else int((orders['Order Zipcode_missing'] == 0).sum()),
        'orders': len(orders), 'sales_tail_rows': int(tail.sum()),
        'sales_tail_total': float(df.loc[tail, 'Sales'].sum()),
        'sales_total': total, 'sales_tail_share_pct': float(df.loc[tail, 'Sales'].sum()/total*100),
        'mean_sales_retained': float(retained.Sales.mean()),
        'mean_sales_if_deleted': float(deleted.Sales.mean()),
        'sales_q1_minmax': float((df.Sales.quantile(.25)-df.Sales.min())/(df.Sales.max()-df.Sales.min())),
        'sales_q3_minmax': float((df.Sales.quantile(.75)-df.Sales.min())/(df.Sales.max()-df.Sales.min())),
    }
    # Numeric-only examples: no IDs, addresses, names, password or email values.
    mism = df[df['late_rule_mismatch'] == 1] if 'late_rule_mismatch' in df else df[(df['Days for shipping (real)'] > df['Days for shipment (scheduled)']).astype(int) != df.Late_delivery_risk]
    cols = ['Shipping Mode', 'Delivery Status', 'Days for shipping (real)',
            'Days for shipment (scheduled)', 'Late_delivery_risk']
    example = mism[cols].head(1).to_dict('records')
    metrics['cancellation_example'] = example
    return pd.DataFrame(scenarios), postal.reset_index(), metrics


def main():
    df = pd.read_csv(BASE/'results/DataCoSupplyChain_Cleaned.csv', low_memory=False)
    scenarios, postal, metrics = calculate(df)
    out = BASE/'results/feedback'; out.mkdir(parents=True, exist_ok=True)
    scenarios.to_csv(out/'denominator_sensitivity.csv', index=False)
    postal.to_csv(out/'postal_coverage_by_market.csv', index=False)
    (out/'evidence.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    print(scenarios.to_string(index=False)); print(postal.to_string(index=False))
    print(json.dumps(metrics, indent=2))


if __name__ == '__main__': main()
