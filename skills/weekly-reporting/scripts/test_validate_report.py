"""Tests for validate_report — the platform-aware marketing/organic reconciliation.

DoorDash attributes its marketing/organic split NET of the promo discount, so those
sum to Net Sales, not gross Total Sales. Checking DD against Total Sales produced ~18
false criticals per run (Santi, goop W27) that would HALT a clean report. Check 2 is
platform-aware now; these tests guard that.

Run: python3 -m unittest test_validate_report -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_report as vr  # noqa: E402


def block(platform):
    """A self-consistent metrics block. Marketing(6000)+Organic sums to Net Sales
    (9000) for DD, and to Total Sales (10000) for UE/GH."""
    return {
        "total_sales": 10000.0, "discounts": 1000.0, "net_sales": 9000.0,
        "commissions": 2800.0, "commissions_pct": 28.0,
        "ad_spend": 500.0, "other_adjustments": 200.0,
        "net_payout": 5500.0, "net_payout_pct": 55.0,
        "total_orders": 300, "orders_from_marketing": 180, "organic_orders": 120,
        "total_marketing_investment": 1500.0, "marketing_investment_pct": 15.0,
        "marketing_driven_sales": 6000.0,
        "organic_sales": 3000.0 if platform == "doordash" else 4000.0,
    }


def criticals(metrics, platform):
    c, _ = vr.validate_metrics(metrics, "[T]", platform)
    return c


class TestMarketingOrganicBase(unittest.TestCase):
    def test_dd_reconciles_to_net_sales(self):
        c = criticals(block("doordash"), "doordash")
        self.assertEqual([m for m in c if "Marketing + Organic" in m], [])

    def test_ue_reconciles_to_total_sales(self):
        c = criticals(block("uber_eats"), "uber_eats")
        self.assertEqual([m for m in c if "Marketing + Organic" in m], [])

    def test_grubhub_reconciles_to_total_sales(self):
        c = criticals(block("grubhub"), "grubhub")
        self.assertEqual([m for m in c if "Marketing + Organic" in m], [])

    def test_dd_net_split_would_false_fail_if_treated_as_total(self):
        # Reproduces the bug: DD's net-based split (sums to 9000) checked against
        # Total Sales (10000) is a false critical. The DD-aware path is clean.
        old = criticals(block("doordash"), None)
        self.assertTrue(any("Marketing + Organic = Total Sales" in m for m in old))
        new = criticals(block("doordash"), "doordash")
        self.assertFalse(any("Marketing + Organic" in m for m in new))

    def test_dd_real_mismatch_still_caught(self):
        b = block("doordash")
        b["organic_sales"] = 2500.0  # 6000 + 2500 = 8500 != net 9000
        c = criticals(b, "doordash")
        self.assertTrue(any("Marketing + Organic = Net Sales" in m for m in c))


if __name__ == "__main__":
    unittest.main()
