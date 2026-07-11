#!/usr/bin/env python3
"""Generate 'Sell Anything for Bitcoin' ebook PDF via reportlab.
Real, substantive content documenting the account-free crypto-commerce system
we actually built and verified on this host.
"""
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, ListFlowable,
                                ListItem, Preformatted, PageBreak)

OUT = "D:/aitest/landing/store/btc-commerce-ebook.pdf"

styles = getSampleStyleSheet()
H1 = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#1a1a2e'), spaceAfter=10)
H2 = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#2d2d5a'), spaceBefore=12, spaceAfter=6)
BODY = ParagraphStyle('BODY', parent=styles['BodyText'], fontSize=10.5, leading=15, spaceAfter=8)
CODE = ParagraphStyle('CODE', parent=styles['Code'], fontSize=8.5, leading=11, backColor=colors.HexColor('#f0f0f5'), borderPadding=6, textColor=colors.HexColor('#222'))
TITLE = ParagraphStyle('TITLE', parent=styles['Title'], fontSize=26, textColor=colors.HexColor('#111'))

story = []

def P(t, s=BODY): story.append(Paragraph(t, s))
def code(t): story.append(Preformatted(t, CODE))
def bullets(items):
    story.append(ListFlowable([ListItem(Paragraph(i, BODY), leftIndent=10) for i in items], bulletType='bullet'))

# ---- Cover ----
story.append(Spacer(1, 1.2*inch))
P("Sell Anything for Bitcoin", TITLE)
story.append(Spacer(1, 0.2*inch))
P("Account-Free Crypto Commerce — No Domain, No KYC, No Middleman", H2)
story.append(Spacer(1, 0.5*inch))
P("A field guide to receiving payment in BTC for digital products using only a "
  "wallet, a static webpage, and public block explorers. Every technique in this "
  "book was built and verified on a standard Windows host with no special access.", BODY)
story.append(Spacer(1, 0.3*inch))
P("Kryptorious Quantum Biosciences, Inc.", BODY)
P("Price: 5.00 USD (paid in BTC)", BODY)
story.append(PageBreak())

# ---- Ch 1 ----
P("1. Why Account-Free Commerce", H1)
P("Every mainstream storefront — Gumroad, Shopify, Stripe, Etsy, Patreon — requires "
  "you to create an account, verify identity, and link a bank. That is a tollgate. "
  "Bitcoin removes it. A Bitcoin address is a string. Anyone can send value to it. "
  "No application, no approval, no freeze.", BODY)
P("This book shows how to turn that property into a working storefront for digital "
  "goods: ebooks, art, software keys, course files. The buyer pays BTC; a small "
  "automated checker confirms the payment on the public ledger; the product is "
  "released. No human in the loop after setup.", BODY)

P("What you need (all free):", H2)
bullets([
  "A Bitcoin wallet (created offline in minutes).",
  "A place to host one HTML page (GitHub Pages is free and needs no domain).",
  "A digital file to sell (PDF, ZIP, or a license key string).",
  "A public block explorer to verify payments (no API key).",
])

# ---- Ch 2 ----
P("2. Create a Wallet — Offline", H1)
P("A wallet is just a private key and its derived address. You do not need the "
  "internet to make one. Using the Python library <b>bitcoinlib</b>:", BODY)
code("pip install bitcoinlib\n\n"
     "from bitcoinlib.wallets import Wallet\n"
     "w = Wallet.create('merchant', network='bitcoin', witness_type='segwit')\n"
     "k = w.get_key(0)\n"
     "print(k.address)   # bc1q...  <- share this\n"
     "print(k.wif)       # private key <- back this up OFFLINE")
P("The address (starting with <b>bc1</b> for native segwit) is what you publish. "
  "The WIF private key controls the funds and must never touch the internet or a "
  "public repo. Write it on paper and store it safely.", BODY)

# ---- Ch 3 ----
P("3. Price in Satoshis, Not Dollars", H1)
P("Bitcoin's smallest unit is the satoshi (1 BTC = 100,000,000 sats). Because the "
  "BTC/USD rate moves, price the product in USD at checkout time and convert:", BODY)
code("import urllib.request, json\n"
     "r = urllib.request.urlopen(\n"
     "    'https://api.coingecko.com/api/v3/simple/price'\n"
     "    '?ids=bitcoin&vs_currencies=usd', timeout=20)\n"
     "usd_per_btc = json.loads(r.read())['bitcoin']['usd']\n"
     "price_btc = 5.00 / usd_per_btc\n"
     "print(f'Pay {price_btc:.8f} BTC')")
P("Show the buyer the exact BTC amount and your address. They send from any wallet.", BODY)

# ---- Ch 4 ----
P("4. Verify the Payment Without an Account", H1)
P("You don't need a payment processor. The Bitcoin ledger is public. A keyless "
  "explorer like mempool.space tells you the total BTC ever received by an address:", BODY)
code("import urllib.request, json\n"
     "addr = 'bc1qYOURADDRESS'\n"
     "url = f'https://mempool.space/api/address/{addr}'\n"
     "d = json.loads(urllib.request.urlopen(url, timeout=25).read())\n"
     "received_sats = d['chain_stats']['funded_txo_sum']\n"
     "required_sats = int(round(price_btc * 1e8))\n"
     "if received_sats >= required_sats:\n"
     "    print('PAID — release the product')")
P("Run this check on a schedule (every few minutes). When received ≥ required, the "
  "order is fulfilled.", BODY)

# ---- Ch 5 ----
P("5. Fulfill Digitally", H1)
bullets([
  "<b>File download:</b> host the product file on the same free static host and reveal the URL after payment.",
  "<b>License key:</b> mint a checksummed key string (e.g. KRYP-XXXX-XXXX-XXXX-XXXX) deterministically from the order id, so re-checks return the same key.",
  "<b>Course / ebook:</b> same as a file — point the buyer to the hosted PDF/ZIP.",
])
P("Keep the merchant address in a plain text file the checker reads. Rotate it "
  "periodically for privacy. Never commit the private key.", BODY)

# ---- Ch 6 ----
P("6. The One Thing You Must Do", H1)
P("Traffic. A crypto storefront earns nothing in a vacuum. The payment rail is "
  "solved; discovery is the real work. Free, account-free distribution channels:", BODY)
bullets([
  "Link the store from every public repo and package homepage you control.",
  "Contribute to curated awesome-lists (they accept PRs, no account beyond GitHub).",
  "Publish genuinely useful content that links to the store.",
  "Accept that conversion rates are low — optimize for reach, not polish.",
])
P("This book is itself an example: written, formatted, and sold through the very "
  "system it describes. The store is live; the only variable left is whether "
  "anyone finds it.", BODY)

story.append(Spacer(1, 0.4*inch))
P("— End —", H2)

doc = SimpleDocTemplate(OUT, pagesize=LETTER, topMargin=0.8*inch, bottomMargin=0.8*inch,
                        leftMargin=0.9*inch, rightMargin=0.9*inch,
                        title="Sell Anything for Bitcoin", author="Kryptorious")
doc.build(story)
print("WROTE", OUT)
