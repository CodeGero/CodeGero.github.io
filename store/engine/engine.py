"""Crypto-commerce engine for Kryptorious — sells products for BTC.

No account, no KYC, no domain. Single source of truth: orders_catalog.json
(a committed pool of per-order UNIQUE BTC addresses derived from the watch-only
MERCHANT_XPUB.txt). The storefront serves slots; the fulfillment poller verifies
each slot's OWN address. One payment can never unlock another order.

The merchant's private key lives ONLY in the operator's local wallet file and is
never read by this engine.
"""
from __future__ import annotations

import binascii
import hashlib
import json
import os
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG_FILE = os.path.join(os.path.dirname(HERE), "orders_catalog.json")

XPUB_FILE = os.path.join(os.path.dirname(HERE), "MERCHANT_XPUB.txt")

CG_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"

# Catalog: product id -> (display name, price USD, fulfillment type)
CATALOG = {
    "devflow-premium": ("DevFlow Premium License (lifetime)", 9.00, "key"),
    "art-pack": ("Serene Gradient Wall Art — 4-Poster Pack", 7.00, "download"),
    "btc-ebook": ("Sell Anything for Bitcoin — Account-Free Commerce eBook (PDF)", 5.00, "download-ebook"),
}

COIN = "bitcoin"

_PRICE_CACHE = {"ts": 0, "usd": None}
_PRICE_MAX_AGE = 900


# --------------------------------------------------------------------------
# Pricing (hardened: never crash on network failure)
# --------------------------------------------------------------------------
def live_prices() -> dict:
    try:
        with urllib.request.urlopen(CG_URL, timeout=20) as r:
            data = json.loads(r.read().decode())
        usd = float(data["bitcoin"]["usd"])
        _PRICE_CACHE["ts"] = time.time()
        _PRICE_CACHE["usd"] = usd
        return {"bitcoin": usd}
    except Exception:
        if _PRICE_CACHE["usd"] is not None:
            return {"bitcoin": _PRICE_CACHE["usd"]}
        raise RuntimeError("CoinGecko unreachable and no cached price available")


def usd_to_coin(amount_usd: float, prices: dict) -> float:
    return round(amount_usd / prices[COIN], 8)


# --------------------------------------------------------------------------
# Per-order receive address (watch-only derivation from MERCHANT_XPUB.txt)
# --------------------------------------------------------------------------
def _load_xpub() -> str:
    if not os.path.exists(XPUB_FILE):
        raise RuntimeError("MERCHANT_XPUB.txt missing - put your watch-only zpub there.")
    return open(XPUB_FILE).read().strip()


def derive_order_address(order_index: int) -> str:
    from bitcoinlib.keys import HDKey
    watch = HDKey.from_wif(_load_xpub(), network="bitcoin")
    return watch.subkey_for_path(f"m/0/{order_index}").address()


# --------------------------------------------------------------------------
# License key minting (mirrors devflow.license._checksum_groups)
# --------------------------------------------------------------------------
_BASE36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _to_base36(n: int) -> str:
    if n == 0:
        return "0"
    out = ""
    while n:
        out = _BASE36[n % 36] + out
        n //= 36
    return out


def _checksum(groups: list[str]) -> str:
    crc = binascii.crc32("".join(groups).encode()) & 0xFFFFFFFF
    return _to_base36(crc).upper().zfill(4)[-4:]


def mint_key(seed: str) -> str:
    h = hashlib.sha256(seed.encode()).hexdigest().upper()
    g = [h[i:i + 4] for i in range(0, 12, 4)]
    return "KRYP-" + "-".join(g) + "-" + _checksum(g)


# --------------------------------------------------------------------------
# Order catalog (single source of truth)
# --------------------------------------------------------------------------
def load_catalog() -> list:
    if not os.path.exists(CATALOG_FILE):
        return []
    with open(CATALOG_FILE) as f:
        return json.load(f)


def _save_catalog(cat: list) -> None:
    with open(CATALOG_FILE, "w") as f:
        json.dump(cat, f, indent=2)


def get_slot(address: str) -> dict | None:
    for s in load_catalog():
        if s["address"] == address:
            return s
    return None


def mark_fulfilled(slot: dict) -> dict:
    if slot["fulfillment"] == "key":
        slot["key"] = mint_key(slot["address"] + ":" + slot["product_id"])
    elif slot["fulfillment"] == "download":
        slot["download"] = "https://codegero.github.io/store/art-pack.zip"
    elif slot["fulfillment"] == "download-ebook":
        slot["download"] = "https://codegero.github.io/store/btc-commerce-ebook.pdf"
    slot["paid"] = True
    slot["fulfilled"] = True
    # persist
    cat = load_catalog()
    for i, s in enumerate(cat):
        if s["address"] == slot["address"]:
            cat[i] = slot
            break
    _save_catalog(cat)
    return slot


# --------------------------------------------------------------------------
# Payment verification (public explorers only — no API key, no account)
# --------------------------------------------------------------------------
def _fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "kryptorious-store/1.0"})
    with urllib.request.urlopen(req, timeout=8) as r:
        return json.loads(r.read().decode())


_EXPLORERS = {
    "bitcoin": [
        lambda a: _fetch_json(f"https://mempool.space/api/address/{a}")["chain_stats"]["funded_txo_sum"],
        lambda a: _fetch_json(f"https://blockstream.info/api/address/{a}")["chain_stats"]["funded_txo_sum"],
    ],
}


def received_total(addr: str, coin: str = COIN) -> int:
    for fn in _EXPLORERS.get(coin, []):
        try:
            return int(fn(addr))
        except Exception:
            continue
    return 0


def verify_payment(slot: dict) -> bool:
    """True only if THIS slot's own address received >= its exact amount."""
    req_sat = int(round(slot["amount"] * 1e8))
    got = received_total(slot["address"], COIN)
    return got >= req_sat
