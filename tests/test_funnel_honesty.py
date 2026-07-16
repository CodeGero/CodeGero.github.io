from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
HTML_FILES = list(ROOT.rglob("*.html"))
ALL_HTML = "\n".join(path.read_text(encoding="utf-8") for path in HTML_FILES)


def product_counts() -> dict[str, int]:
    match = re.search(r"const P=(\[.*?\]);\s*\n", INDEX, re.DOTALL)
    assert match, "product grid array missing"
    payload = match.group(1)
    return {
        "all": payload.count("{n:"),
        "pypi": payload.count('p:"pypi"'),
        "github": payload.count('p:"github"'),
        "npm": payload.count('p:"npm"'),
    }


def test_visible_fleet_counts_match_the_actual_product_grid():
    counts = product_counts()
    assert counts == {"all": 32, "pypi": 12, "github": 15, "npm": 5}
    assert f'All<span class="count">{counts["all"]}</span>' in INDEX
    assert f'PyPI<span class="count">{counts["pypi"]}</span>' in INDEX
    assert f'GitHub Actions<span class="count">{counts["github"]}</span>' in INDEX
    assert f'npm<span class="count">{counts["npm"]}</span>' in INDEX
    assert f'data-target="{counts["github"]}">0</div><div class="stat-label">GitHub Actions' in INDEX


def test_every_sales_link_uses_the_operational_bitcoin_store_not_gumroad():
    lowered = ALL_HTML.lower()
    assert "gumroad" not in lowered
    assert "jbvet" not in lowered
    assert "https://codegero.github.io/store/" in INDEX


def test_pages_do_not_sell_support_or_premium_features_that_do_not_exist():
    lowered = ALL_HTML.lower()
    unsupported = [
        "private slack",
        "priority email",
        "coverage dashboards",
        "multi-project health reports",
        "apiguard premium",
        "config tools premium",
        "bulk changelog generation",
        "cloud sarif dashboards",
        "scheduled baseline diffs",
        "html trend reports",
    ]
    assert [claim for claim in unsupported if claim in lowered] == []


def test_current_marketing_does_not_use_stale_fleet_counts():
    lowered = ALL_HTML.lower()
    assert "33 tools" not in lowered
    assert "33-tool" not in lowered
    assert "16 github actions" not in lowered
    assert "16 actions total" not in lowered


def test_pages_do_not_claim_an_unverified_incorporated_entity():
    assert "Quantum Biosciences, Inc." not in ALL_HTML


def test_blog_index_and_current_ctas_use_verified_32_tool_count():
    blog_index = (ROOT / "blog" / "index.html").read_text(encoding="utf-8")
    assert "32 free MIT-licensed developer tools" in blog_index
    assert "Get all 32 tools" in blog_index
