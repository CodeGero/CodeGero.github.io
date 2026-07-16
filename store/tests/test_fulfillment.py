from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

MODULE_PATH = Path(__file__).parents[1] / "engine" / "fulfill_cron.py"
SPEC = importlib.util.spec_from_file_location("fulfill_cron", MODULE_PATH)
fulfill_cron = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = fulfill_cron
SPEC.loader.exec_module(fulfill_cron)


def test_publish_catalog_commits_and_pushes_when_catalog_changed(tmp_path):
    calls: list[tuple[list[str], Path]] = []

    def runner(args, cwd, **kwargs):
        calls.append((list(args), Path(cwd)))
        if args[:3] == ["git", "status", "--porcelain"]:
            return fulfill_cron.CommandResult(0, " M store/orders_catalog.json\n", "")
        return fulfill_cron.CommandResult(0, "", "")

    changed = fulfill_cron.publish_catalog(tmp_path, runner=runner)

    assert changed is True
    assert [args for args, _ in calls] == [
        ["git", "status", "--porcelain", "--", "store/orders_catalog.json"],
        ["git", "add", "--", "store/orders_catalog.json"],
        ["git", "commit", "-m", "fulfill paid BTC order"],
        ["git", "push", "origin", "main"],
    ]
    assert all(cwd == tmp_path for _, cwd in calls)


def test_publish_catalog_is_a_noop_when_catalog_is_clean(tmp_path):
    def runner(args, cwd, **kwargs):
        return fulfill_cron.CommandResult(0, "", "")

    assert fulfill_cron.publish_catalog(tmp_path, runner=runner) is False


def test_publish_catalog_fails_loudly_when_push_fails(tmp_path):
    def runner(args, cwd, **kwargs):
        if args[:3] == ["git", "status", "--porcelain"]:
            return fulfill_cron.CommandResult(0, " M store/orders_catalog.json\n", "")
        if args[:2] == ["git", "push"]:
            return fulfill_cron.CommandResult(1, "", "authentication failed")
        return fulfill_cron.CommandResult(0, "", "")

    with pytest.raises(RuntimeError, match="git push"):
        fulfill_cron.publish_catalog(tmp_path, runner=runner)


def test_main_always_publishes_any_pending_catalog_change(monkeypatch, tmp_path):
    xpub = tmp_path / "xpub.txt"
    xpub.write_text("public-watch-only-key")
    monkeypatch.setattr(fulfill_cron, "XPUB_FILE", str(xpub))
    monkeypatch.setattr(fulfill_cron, "load_catalog", lambda: [{"slot": 1, "fulfilled": False}])
    monkeypatch.setattr(fulfill_cron, "verify_payment", lambda slot: False)
    published: list[bool] = []
    monkeypatch.setattr(fulfill_cron, "publish_catalog", lambda: published.append(True) or False)

    fulfill_cron.main()

    assert published == [True]


def test_main_does_not_print_a_reusable_license_key(monkeypatch, tmp_path, capsys):
    xpub = tmp_path / "xpub.txt"
    xpub.write_text("public-watch-only-key")
    monkeypatch.setattr(fulfill_cron, "XPUB_FILE", str(xpub))
    monkeypatch.setattr(fulfill_cron, "load_catalog", lambda: [{"slot": 7, "fulfilled": False, "product_id": "devflow-premium"}])
    monkeypatch.setattr(fulfill_cron, "verify_payment", lambda slot: True)
    monkeypatch.setattr(
        fulfill_cron,
        "mark_fulfilled",
        lambda slot: {**slot, "fulfilled": True, "key": "KRYP-SECRET-LICENSE"},
    )
    monkeypatch.setattr(fulfill_cron, "publish_catalog", lambda: True)

    fulfill_cron.main()

    output = capsys.readouterr().out
    assert "FULFILLED slot 7 (devflow-premium)" in output
    assert "KRYP-SECRET-LICENSE" not in output
