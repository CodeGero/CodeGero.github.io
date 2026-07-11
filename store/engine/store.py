#!/usr/bin/env python3
"""Kryptorious crypto store — CLI.

Usage:
  python store.py catalog
  python store.py order <product_id> <btc|ltc> <merchant_address>
  python store.py check <order_id> <merchant_address>
  python store.py fulfill <order_id>

The merchant_address is a plain crypto address string — no account, no KYC.
"""
from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import (CATALOG, create_order, live_prices, load_order,
                    verify_payment, fulfill, usd_to_coin)


def main(argv):
    if len(argv) < 2:
        print(__doc__); return 1
    cmd = argv[1]

    if cmd == "catalog":
        for pid, (name, usd, ftype) in CATALOG.items():
            print(f"  {pid:18} ${usd:.2f}  [{ftype}]  {name}")
        return 0

    if cmd == "order":
        if len(argv) < 5:
            print("usage: store.py order <product_id> <btc|ltc> <address>"); return 1
        pid, coin, addr = argv[2], argv[3].lower(), argv[4]
        try:
            prices = live_prices()
        except Exception as e:
            print("price fetch failed:", e); return 1
        o = create_order(pid, coin, prices)
        print(f"\n  ORDER {o['order_id']}")
        print(f"  Product : {o['product']}")
        print(f"  Pay     : {o['amount']:.8f} {coin.upper()}  (~${o['usd']:.2f})")
        print(f"  To      : {addr}")
        print(f"  Check   : python store.py check {o['order_id']} {addr}")
        return 0

    if cmd == "check":
        if len(argv) < 4:
            print("usage: store.py check <order_id> <address>"); return 1
        oid, addr = argv[2], argv[3]
        o = load_order(oid)
        if not o:
            print("unknown order"); return 1
        paid = verify_payment(o, addr)
        print(f"  Order {oid}: required {o['amount']:.8f} {o['coin'].upper()}")
        print(f"  Payment detected: {'YES' if paid else 'not yet'}")
        if paid and not o.get("fulfilled"):
            o = fulfill(o)
        if o.get("fulfilled"):
            if o.get("key"):
                print(f"  LICENSE KEY: {o['key']}")
            if o.get("download"):
                print(f"  DOWNLOAD   : {o['download']}")
        return 0

    if cmd == "fulfill":
        if len(argv) < 3:
            print("usage: store.py fulfill <order_id>"); return 1
        o = load_order(argv[2])
        if not o:
            print("unknown order"); return 1
        o = fulfill(o)
        print("fulfilled:", o.get("key") or o.get("download"))
        return 0

    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
