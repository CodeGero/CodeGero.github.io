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

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import sys
from typing import Callable, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
LANDING_ROOT = Path(HERE).parents[1]
sys.path.insert(0, HERE)

try:
    from engine import load_catalog, verify_payment, mark_fulfilled
except Exception as e:
    print("import failed:", e); sys.exit(0)

XPUB_FILE = os.path.join(os.path.dirname(HERE), "MERCHANT_XPUB.txt")


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


def _run(args: Sequence[str], cwd: Path, **_: object) -> CommandResult:
    result = subprocess.run(
        list(args), cwd=cwd, text=True, capture_output=True, check=False
    )
    return CommandResult(result.returncode, result.stdout, result.stderr)


def publish_catalog(
    landing_root: Path = LANDING_ROOT,
    *,
    runner: Callable[..., CommandResult] = _run,
) -> bool:
    """Commit and publish a changed catalog so buyers can receive fulfillment."""
    commands = [
        ["git", "status", "--porcelain", "--", "store/orders_catalog.json"],
        ["git", "add", "--", "store/orders_catalog.json"],
        ["git", "commit", "-m", "fulfill paid BTC order"],
        ["git", "push", "origin", "main"],
    ]
    status = runner(commands[0], cwd=landing_root)
    if status.returncode != 0:
        raise RuntimeError(f"git status failed: {status.stderr.strip()}")
    if not status.stdout.strip():
        return False
    for command in commands[1:]:
        result = runner(command, cwd=landing_root)
        if result.returncode != 0:
            raise RuntimeError(f"{' '.join(command[:2])} failed: {result.stderr.strip()}")
    return True


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
                print(f"FULFILLED slot {s['slot']} ({s['product_id']})")
        except Exception as e:
            print(f"CHECK_ERROR slot {s['slot']}: {e}")

    published = publish_catalog()
    if published:
        print("PUBLISHED fulfilled order catalog.")
    if fulfilled == 0:
        print("POLLED", len(cat), "slots - none paid yet.")


if __name__ == "__main__":
    main()
