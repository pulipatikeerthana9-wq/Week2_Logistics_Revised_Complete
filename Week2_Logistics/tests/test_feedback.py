import unittest
import pandas as pd
from feedback_analysis import calculate


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.df=pd.DataFrame({'Order Id':[1,1,2,3], 'Delivery Status':['Late delivery','Late delivery','Shipping canceled','On time'],
          'Late_delivery_risk':[1,1,0,0],'Market':['USCA','USCA','Europe','USCA'],
          'Order Zipcode_missing':[0,0,1,1],'Sales':[100.,100.,1000.,200.], 'Sales_iqr_flag':[0,0,1,0],
          'Shipping Mode':['Standard Class']*4,'Days for shipping (real)':[3,3,4,2],
          'Days for shipment (scheduled)':[2,2,2,2]})
    def test_order_denominator(self):
        t=calculate(self.df)[0];self.assertEqual(t.records.tolist(),[4,3,3,2])
        self.assertAlmostEqual(t.late_rate_pct.iloc[3],50)
    def test_postal_at_order_grain(self):
        t=calculate(self.df)[1].set_index('Market')
        self.assertEqual(t.loc['USCA','orders'],2);self.assertEqual(t.loc['USCA','known'],1)
    def test_tail_accounting(self):
        m=calculate(self.df)[2]
        self.assertEqual(m['sales_tail_rows'],1);self.assertEqual(m['sales_tail_total'],1000)
        self.assertAlmostEqual(m['mean_sales_if_deleted'],400/3)
    def test_example_has_no_identifier(self):
        m=calculate(self.df)[2]
        self.assertNotIn('Order Id',m['cancellation_example'][0])


if __name__=='__main__': unittest.main()
