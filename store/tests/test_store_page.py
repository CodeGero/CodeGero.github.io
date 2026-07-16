from __future__ import annotations

from pathlib import Path

STORE = Path(__file__).parents[1]
PAGE = (STORE / "index.html").read_text(encoding="utf-8")
APP = STORE / "checkout-app.mjs"


def test_store_uses_tested_checkout_controller_instead_of_inline_first_slot_logic():
    assert '<script type="module" src="./checkout-app.mjs"></script>' in PAGE
    assert "cat.find(" not in PAGE
    assert APP.exists()


def test_store_describes_real_confirmation_latency_and_browser_local_reservation():
    lowered = PAGE.lower()
    assert "instant delivery" not in lowered
    assert "a unique order is created" not in lowered
    assert "browser" in lowered
    assert "confirmation" in lowered


def test_store_does_not_claim_an_unverified_corporate_entity_or_kyc_property():
    assert "Quantum Biosciences, Inc." not in PAGE
    assert "No KYC" not in PAGE


def test_store_keeps_paid_download_urls_out_of_page_source():
    assert "art-pack.zip" not in PAGE
    assert "btc-commerce-ebook.pdf" not in PAGE


def test_checkout_has_a_no_javascript_failure_message():
    assert "<noscript>" in PAGE
    assert "JavaScript is required" in PAGE
