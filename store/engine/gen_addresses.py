#!/usr/bin/env python3
"""Generate a static pool of per-order BTC addresses for the storefront.

Writes store/orders_catalog.json: a list of order slots, each with a UNIQUE
receive address derived from MERCHANT_XPUB.txt, the product, and the live USD
price converted to BTC. The storefront serves these; the fulfillment poller
verifies each address independently (no shared-address over-fulfillment).

Run after MERCHANT_XPUB.txt exists and whenever you change prices or want more
slots. Committed to the repo (addresses are public; the private key is NOT).
"""
from __future__ import annotations
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from engine import CATALOG, _load_xpub, derive_order_address, usd_to_coin, live_prices

OUT = os.path.join(os.path.dirname(HERE), "orders_catalog.json")
POOL_PER_PRODUCT = 8


def main():
    _load_xpub()  # ensure present
    prices = live_prices()
    catalog = []
    idx = 0
    for pid, (name, usd, ftype) in CATALOG.items():
        amt = usd_to_coin(usd, prices)
        for _ in range(POOL_PER_PRODUCT):
            catalog.append({
                "slot": idx,
                "address": derive_order_address(idx),
                "product_id": pid,
                "product": name,
                "amount": amt,
                "usd": usd,
                "fulfillment": ftype,
                "paid": False,
                "fulfilled": False,
            })
            idx += 1
    with open(OUT, "w") as f:
        json.dump(catalog, f, indent=2)
    print(f"wrote {len(catalog)} order slots to {OUT}")


if __name__ == "__main__":
    main()
