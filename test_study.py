from datetime import date
from math import log
import unittest

import numpy as np

from study import accounts, blocks, components, shifted_month


class CarryTests(unittest.TestCase):
    def test_zero_carry_and_quote_inversion(self):
        a=components([[log(140/150),0,0,1/365]],0)[0]
        self.assertAlmostEqual(a[0],1-150/140)
        self.assertAlmostEqual(a[1:].sum(),0)
        self.assertGreater(components([[log(150/140),0,0,1/365]],0)[0,0],0)

    def test_no_fx_move_and_exact_cash_ledger(self):
        self.assertAlmostEqual(components([[0,.01,.003,.1]],100).sum(),.006)
        row=[log(145/150),.001,.0004,.02]
        direct=1+row[1]-(150/145)*(1+row[2]+.005*row[3])
        self.assertAlmostEqual(components([row],50).sum(),direct)

    def test_margin_and_stop(self):
        result,_,breach=accounts(np.array([[-.07,.09]]),10)
        self.assertTrue(breach[0])
        self.assertAlmostEqual(result[0],-.702)

    def test_sampling_and_two_month_lag(self):
        sample=blocks(np.random.default_rng(41),np.arange(60),10,12,4)
        np.testing.assert_array_equal(np.diff(sample[:,0:4],axis=1),1)
        self.assertEqual(shifted_month(date(2024,1,3),-2),date(2023,11,1))
