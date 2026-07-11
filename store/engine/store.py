#!/usr/bin/env python3
"""Kryptorious crypto store — CLI.

Usage:
  python store.py catalog          # list products
  python store.py slots            # show order slots + paid status
  python store.py poll             # verify all slots, fulfill any paid
  python store.py check <address>  # verify one slot by address

Per-order unique BTC addresses are derived from MERCHANT_XPUB.txt (watch-only).
The private key is never touched by this CLI.
"""
from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import CATALOG, load_catalog, verify_payment, mark_fulfilled, get_slot


def main(argv):
    if len(argv) < 2:
        print(__doc__); return 1
    cmd = argv[1]

    if cmd == "catalog":
        for pid, (name, usd, ftype) in CATALOG.items():
            print(f"  {pid:18} ${usd:.2f}  [{ftype}]  {name}")
        return 0

    if cmd == "slots":
        cat = load_catalog()
        paid = sum(1 for s in cat if s.get("fulfilled"))
        print(f"  {len(cat)} slots, {paid} fulfilled")
        for s in cat[:5]:
            print(f"  [{s['slot']}] {s['product_id']:14} {s['amount']:.8f} -> {s['address'][:14]}… paid={s.get('paid')}")
        return 0

    if cmd == "poll":
        cat = load_catalog()
        done = 0
        for s in cat:
            if s.get("fulfilled"):
                continue
            if verify_payment(s):
                s = mark_fulfilled(s)
                done += 1
                print(f"  FULFILLED slot {s['slot']} ({s['product_id']}) -> {s.get('key') or s.get('download')}")
        if done == 0:
            print("  POLLED - no new payments.")
        return 0

    if cmd == "check":
        if len(argv) < 3:
            print("usage: store.py check <address>"); return 1
        s = get_slot(argv[2])
        if not s:
            print("unknown address"); return 1
        paid = verify_payment(s)
        print(f"  slot {s['slot']} {s['product_id']}: required {s['amount']:.8f} BTC")
        print(f"  payment detected: {'YES' if paid else 'not yet'}")
        if paid and not s.get("fulfilled"):
            s = mark_fulfilled(s)
            print(f"  delivered: {s.get('key') or s.get('download')}")
        return 0

    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
