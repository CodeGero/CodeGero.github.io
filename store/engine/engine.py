"""Crypto-commerce engine for Kryptorious — sells DevFlow Premium & art packs for BTC/LTC.

No account, no KYC, no domain. The only external input is a wallet ADDRESS
(a string). Payment is verified against public block explorers; fulfillment
mints a real, self-validating DevFlow Premium license key (CRC32-checksummed
KRYP-XXXX-XXXX-XXXX-XXXX, same algorithm devflow uses offline) or reveals a
download link.

This module never holds secrets. The merchant address is supplied at runtime.
"""
from __future__ import annotations

import binascii
import hashlib
import json
import os
import time
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
ORDERS_DIR = os.path.join(HERE, "orders")
os.makedirs(ORDERS_DIR, exist_ok=True)

CG_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,litecoin&vs_currencies=usd"
# Blockchain.com explorer API (no key). Known-stable public endpoint.
EXPLORER_API = "https://blockchain.info/q/addressreceivetotal/{addr}"
# Backup: Blockstream Esplora (also no key), used if blockchain.info fails.
ESPLORA_API = "https://blockstream.info/api/address/{addr}"

# Catalog: product id -> (display name, price USD, fulfillment type)
CATALOG = {
    "devflow-premium": ("DevFlow Premium License (lifetime)", 9.00, "key"),
    "art-pack": ("Serene Gradient Wall Art — 4-Poster Pack", 7.00, "download"),
}

# We accept BTC only. Every LTC explorer tested from this host is blocked
# (HTTP 430/403), so we will not advertise a rail we cannot verify.
COIN = "bitcoin"


# --------------------------------------------------------------------------
# Pricing
# --------------------------------------------------------------------------
def live_prices() -> dict:
    """Return {'bitcoin': usd, 'litecoin': usd} from CoinGecko. Raises on failure."""
    with urllib.request.urlopen(CG_URL, timeout=20) as r:
        data = json.loads(r.read().decode())
    return {"bitcoin": float(data["bitcoin"]["usd"]),
            "litecoin": float(data["litecoin"]["usd"])}


def usd_to_coin(amount_usd: float, coin: str, prices: dict) -> float:
    """Convert USD to a coin amount with 8-decimal precision.

    prices keys are CoinGecko ids: 'bitcoin', 'litecoin' (we use BTC only).
    """
    key = "bitcoin" if coin in ("btc", "bitcoin") else "litecoin"
    rate = prices[key]
    amt = amount_usd / rate
    return round(amt, 8)


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
    """Mint a valid KRYP-XXXX-XXXX-XXXX-XXXX key deterministically from a seed.

    Deterministic so re-fulfilling the same order yields the same key.
    """
    h = hashlib.sha256(seed.encode()).hexdigest().upper()
    g = [h[i:i + 4] for i in range(0, 12, 4)]  # 3 groups of 4 hex
    return "KRYP-" + "-".join(g) + "-" + _checksum(g)


# --------------------------------------------------------------------------
# Order persistence
# --------------------------------------------------------------------------
def create_order(product_id: str, coin: str, prices: dict) -> dict:
    if product_id not in CATALOG:
        raise ValueError(f"unknown product {product_id}")
    name, usd, ftype = CATALOG[product_id]
    amount = usd_to_coin(usd, coin, prices)
    order_id = hashlib.sha256(f"{product_id}{coin}{time.time()}".encode()).hexdigest()[:12]
    order = {
        "order_id": order_id,
        "product_id": product_id,
        "product": name,
        "coin": coin,
        "amount": amount,
        "usd": usd,
        "fulfillment": ftype,
        "created": int(time.time()),
        "paid": False,
        "fulfilled": False,
    }
    _save(order)
    return order


def _save(order: dict) -> None:
    with open(os.path.join(ORDERS_DIR, order["order_id"] + ".json"), "w") as f:
        json.dump(order, f, indent=2)


def load_order(order_id: str) -> dict | None:
    p = os.path.join(ORDERS_DIR, order_id + ".json")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)


# --------------------------------------------------------------------------
# Payment verification (public explorers only — no API key, no account)
# --------------------------------------------------------------------------
def _fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "kryptorious-store/1.0"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode())


def _fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "kryptorious-store/1.0"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode().strip()


# Public, keyless BTC explorers. First working wins.
_EXPLORERS = {
    "bitcoin": [
        lambda a: _fetch_json(f"https://mempool.space/api/address/{a}")["chain_stats"]["funded_txo_sum"],
        lambda a: _fetch_json(f"https://blockstream.info/api/address/{a}")["chain_stats"]["funded_txo_sum"],
    ],
}


def received_total(addr: str, coin: str = "bitcoin") -> int:
    """Total satoshis ever received by addr, via public explorers (no API key).

    Returns int satoshis. Falls back across explorers per coin.
    """
    for fn in _EXPLORERS.get(coin, []):
        try:
            val = int(fn(addr))
            return val
        except Exception:
            continue
    return 0


def verify_payment(order: dict, addr: str) -> bool:
    """Return True if addr has received >= order amount (in satoshis)."""
    coin = order["coin"]
    req_sat = int(round(order["amount"] * 1e8))
    got = received_total(addr, coin)
    return got >= req_sat


# --------------------------------------------------------------------------
# Fulfillment
# --------------------------------------------------------------------------
def fulfill(order: dict) -> dict:
    """Mark order paid+fulfilled and produce the deliverable."""
    if order["fulfillment"] == "key":
        key = mint_key(order["order_id"] + ":" + order["product_id"])
        order["key"] = key
    elif order["fulfillment"] == "download":
        order["download"] = "https://codegero.github.io/store/art-pack.zip"
    order["paid"] = True
    order["fulfilled"] = True
    _save(order)
    return order
