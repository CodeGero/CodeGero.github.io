#!/usr/bin/env python3
"""Autonomous crypto-store fulfillment poller.

Looks for unpaid orders in store/engine/orders/, checks each merchant BTC
address for received funds via public explorer, and auto-fulfills (mints a
real DevFlow license key or reveals the download link) when payment is seen.

Requires: store/MERCHANT_BTC.txt containing ONE line = the merchant BTC address.
If the file is missing/empty, the poller prints a clear instruction and exits
(so it is safe to run on a schedule before the address is set).

Run from the landing repo root (workdir) so relative paths resolve.
"""
from __future__ import annotations
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from engine import load_order, verify_payment, fulfill, ORDERS_DIR
except Exception as e:
    print("import failed:", e); sys.exit(0)

MERCHANT_FILE = os.path.join(os.path.dirname(HERE), "MERCHANT_BTC.txt")


def main():
    if not os.path.exists(MERCHANT_FILE):
        print("NO_MERCHANT_ADDRESS: create store/MERCHANT_BTC.txt with your BTC address.")
        return
    addr = open(MERCHANT_FILE).read().strip()
    if not addr:
        print("NO_MERCHANT_ADDRESS: store/MERCHANT_BTC.txt is empty.")
        return

    pending = []
    if os.path.isdir(ORDERS_DIR):
        for fn in os.listdir(ORDERS_DIR):
            if not fn.endswith(".json"):
                continue
            o = load_order(fn[:-5])
            if o and not o.get("fulfilled"):
                pending.append(o)

    if not pending:
        print("NO_PENDING_ORDERS")
        return

    fulfilled = 0
    for o in pending:
        try:
            if verify_payment(o, addr):
                o = fulfill(o)
                fulfilled += 1
                if o.get("key"):
                    print(f"FULFILLED {o['order_id']} -> KEY {o['key']}")
                elif o.get("download"):
                    print(f"FULFILLED {o['order_id']} -> DOWNLOAD {o['download']}")
        except Exception as e:
            print(f"CHECK_ERROR {o.get('order_id')}: {e}")

    if fulfilled == 0:
        print("POLLED", len(pending), "pending orders — none paid yet.")


if __name__ == "__main__":
    main()
