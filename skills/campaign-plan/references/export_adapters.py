#!/usr/bin/env python3
"""Parse the real platform campaign exports into the engine's unified ads_rows / offers_rows.

The campaign-plan engine ingests campaign performance straight from the platform exports Santi
drops in `Campaign Plan Inputs/<week>/` — no dependency on weekly-reporting. Supported files
(matched by filename):

  ads (Sponsored Listings):
    campaigns_summary_metrics*.csv          -> Uber Eats (weekly, per campaign)
    MARKETING_SPONSORED_LISTING*.csv        -> DoorDash (daily per campaign x store; summed)
  offers (promotions):
    offers-campaigns*.csv                   -> Uber Eats (no spend column — UE doesn't report it)
    MARKETING_PROMOTION*.csv                -> DoorDash (daily; promo spend = "Funded by you")

Output dicts use the same keys the v2 aggregators already consume (Campaign/Platform/Location/
Spend/Attributed Sales/Orders/Impressions/Clicks/New Customers; Promotion/Promo Spend/etc).
"""
from __future__ import annotations
import csv
import glob
import os
import re


def _num(v) -> float:
    s = str(v).replace("$", "").replace(",", "").replace("%", "").replace("x", "").strip()
    if s in ("", "None", "--", "n/a", "—"):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def _loc(name) -> str:
    """'goop kitchen (Venice)' -> 'Venice'; '(North Hollywood, CA)' -> 'North Hollywood';
    '(Silver Lake @ Echo Park Eats)' -> 'Silver Lake'. A bare count ('3'/'4') -> multi-location."""
    name = str(name).strip()
    m = re.search(r"\(([^)]*)\)", name)
    s = (m.group(1) if m else name).split("@")[0].split(",")[0].strip()
    if not s or s.isdigit():
        return "(multi-location)"
    return s


def _audience(campaign_name) -> str:
    n = str(campaign_name).lower()
    if "lapsed" in n:
        return "Lapsed"
    if "new" in n:
        return "New"
    return "All"


def _read(path: str) -> list:
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def ue_sponsored_listings(rows: list) -> list:
    agg: dict = {}
    for r in rows:
        camp = (r.get("Campaign name") or "").strip()
        if not camp:
            continue
        key = (camp, _loc(r.get("Locations", "")))
        d = agg.setdefault(key, {"imp": 0, "clk": 0, "spend": 0, "orders": 0, "sales": 0, "newcx": 0,
                                 "status": r.get("Off/On") or r.get("Status", "")})
        d["imp"] += _num(r.get("Impressions")); d["clk"] += _num(r.get("Clicks"))
        d["spend"] += _num(r.get("Ad spend")); d["orders"] += _num(r.get("Orders"))
        d["sales"] += _num(r.get("Sales")); d["newcx"] += _num(r.get("New customers to brand"))
    out = []
    for (camp, loc), d in agg.items():
        out.append({"Campaign": camp, "Platform": "Uber Eats", "Audience": _audience(camp), "Location": loc,
                    "Impressions": int(d["imp"]), "Clicks": int(d["clk"]), "Spend": d["spend"],
                    "Orders": int(d["orders"]), "Attributed Sales": d["sales"], "New Customers": int(d["newcx"]),
                    "Status": "Off" if str(d["status"]).strip().lower() in ("off", "false") else "Live"})
    return out


def dd_sponsored_listings(rows: list) -> list:
    agg: dict = {}
    for r in rows:
        camp = (r.get("Campaign name") or "").strip()
        if not camp:
            continue
        key = (camp, _loc(r.get("Store name", "")))
        d = agg.setdefault(key, {"imp": 0, "clk": 0, "spend": 0, "orders": 0, "sales": 0, "newcx": 0})
        d["imp"] += _num(r.get("Impressions")); d["clk"] += _num(r.get("Clicks"))
        d["spend"] += _num(r.get("Marketing fees | (including any applicable taxes)"))
        d["orders"] += _num(r.get("Orders")); d["sales"] += _num(r.get("Sales"))
        d["newcx"] += _num(r.get("New customers acquired"))
    out = []
    for (camp, loc), d in agg.items():
        out.append({"Campaign": camp, "Platform": "DoorDash", "Audience": _audience(camp), "Location": loc,
                    "Impressions": int(d["imp"]), "Clicks": int(d["clk"]), "Spend": d["spend"],
                    "Orders": int(d["orders"]), "Attributed Sales": d["sales"], "New Customers": int(d["newcx"]),
                    "Status": "Live"})
    return out


def ue_offers(rows: list) -> list:
    out = []
    for r in rows:
        offer = (r.get("Offer type") or "").strip()
        if not offer:
            continue
        st = str(r.get("Status", "")).strip().lower()
        sales, orders = _num(r.get("Sales (USD)")), _num(r.get("Orders"))
        if sales <= 0 and orders <= 0:
            continue  # drove nothing this week — skip (kills canceled noise + $0 never-ran dupes
            # like the two same-named "Free Item" offers, one real, one empty)
        out.append({"Promotion": offer, "Platform": "Uber Eats", "Locations": _loc(r.get("Stores", "")),
                    "Audience": r.get("Audience", "All"), "Threshold": "—", "Discount": "—",
                    "Redemptions": int(_num(r.get("Orders"))), "Attributed Sales": _num(r.get("Sales (USD)")),
                    "Promo Spend": "n/a",  # UE export carries no offer spend (Merchant Portal only)
                    "New Customers": int(_num(r.get("New customers"))), "% New": "—",
                    "Status": "Ended" if st in ("completed", "canceled", "cancelled") else "Live"})
    return out


def dd_promotions(rows: list) -> list:
    agg: dict = {}
    for r in rows:
        camp = (r.get("Campaign name") or "").strip()
        if not camp:
            continue
        key = (camp, _loc(r.get("Store name", "")))
        d = agg.setdefault(key, {"orders": 0, "sales": 0, "spend": 0, "newcx": 0})
        d["orders"] += _num(r.get("Orders")); d["sales"] += _num(r.get("Sales"))
        d["spend"] += _num(r.get("Customer discounts from marketing | (Funded by you)"))
        d["newcx"] += _num(r.get("New customers acquired"))
    out = []
    for (camp, loc), d in agg.items():
        out.append({"Promotion": camp, "Platform": "DoorDash", "Locations": loc, "Audience": _audience(camp),
                    "Threshold": "—", "Discount": "—", "Redemptions": int(d["orders"]),
                    "Attributed Sales": d["sales"], "Promo Spend": d["spend"], "New Customers": int(d["newcx"]),
                    "% New": f"{d['newcx'] / d['orders'] * 100:.0f}%" if d["orders"] else "—", "Status": "Live"})
    return out


def load_campaign_exports(inputs_dir: str):
    """Scan an inputs dir for known platform exports → (ads_rows, offers_rows). Skips daily UE
    granular + the *_Store self-serve variants (redundant with the summary/MARKETING files)."""
    ads, offers, used = [], [], []
    for p in sorted(glob.glob(os.path.join(inputs_dir, "*.csv"))):
        n = os.path.basename(p).lower()
        try:
            if "campaigns_summary_metrics" in n:
                ads += ue_sponsored_listings(_read(p)); used.append(n)
            elif "marketing_sponsored_listing" in n:
                ads += dd_sponsored_listings(_read(p)); used.append(n)
            elif n.startswith("offers-campaigns"):
                offers += ue_offers(_read(p)); used.append(n)
            elif "marketing_promotion" in n:
                offers += dd_promotions(_read(p)); used.append(n)
        except Exception as e:
            print(f"   (adapter skipped {n}: {str(e)[:70]})")
    return ads, offers, used
