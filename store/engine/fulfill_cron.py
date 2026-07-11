#!/usr/bin/env python3
"""Autonomous crypto-store fulfillment poller (run on a schedule).

Reads store/orders_catalog.json, verifies each slot's OWN unique BTC address
via public explorers, and fulfills (mints a DevFlow key or reveals a download)
when payment is seen. Per-order addresses mean one payment can never unlock
another order.

Requires: store/MERCHANT_XPUB.txt = watch-only zpub (public-safe).
If missing/empty, prints a clear instruction and exits (safe no-op).
"""
from __future__ import annotations
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from engine import load_catalog, verify_payment, mark_fulfilled
except Exception as e:
    print("import failed:", e); sys.exit(0)

XPUB_FILE = os.path.join(os.path.dirname(HERE), "MERCHANT_XPUB.txt")


def main():
    if not os.path.exists(XPUB_FILE) or not open(XPUB_FILE).read().strip():
        print("NO_XPUB: create store/MERCHANT_XPUB.txt with your watch-only zpub.")
        return

    cat = load_catalog()
    if not cat:
        print("NO_CATALOG: run gen_addresses.py first.")
        return

    fulfilled = 0
    for s in cat:
        if s.get("fulfilled"):
            continue
        try:
            if verify_payment(s):
                s = mark_fulfilled(s)
                fulfilled += 1
                print(f"FULFILLED slot {s['slot']} ({s['product_id']}) -> {s.get('key') or s.get('download')}")
        except Exception as e:
            print(f"CHECK_ERROR slot {s['slot']}: {e}")

    if fulfilled == 0:
        print("POLLED", len(cat), "slots - none paid yet.")


if __name__ == "__main__":
    main()
