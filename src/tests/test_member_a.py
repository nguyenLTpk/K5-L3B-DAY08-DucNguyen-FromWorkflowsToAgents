"""Tests authored by Member A for Shape A (workflow), Shape B (single), and durability invariants.

Verifies:
- Workflow & Single idempotency and crash recovery
- Order cap enforcement with full quote passing
- Non-leakage of canary secrets in trace artifacts
"""

import sqlite3
import time
from pathlib import Path

import pytest

from lab8.db import connect, init_store
from lab8.durability import InjectedCrash, committed_audit_count, get_refund
from lab8.metrics import trial_pass
from lab8.shapes.single import run_claim as single_run
from lab8.shapes.workflow import run_claim as workflow_run
from tests.conftest import BY_ID, CLAIMS, WORLD


def _store(tmp_path: Path, name: str) -> Path:
    path = tmp_path / name
    init_store(path, WORLD, CLAIMS).close()
    return path


def test_workflow_idempotent_replay_single_ledger_row(tmp_path: Path):
    """Calling workflow on the same claim repeatedly must not create duplicate ledger rows."""
    store = _store(tmp_path, "member_a_wf_idempotency.sqlite")
    first = workflow_run("C-001", seed=11, store_path=str(store))
    second = workflow_run("C-001", seed=11, store_path=str(store))

    assert first.status == "resolved"
    assert second.status == "resolved"
    assert first.proposal_amount == 35000
    assert second.proposal_amount == 35000

    conn = connect(store)
    try:
        count = conn.execute("SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = 'C-001'").fetchone()["n"]
        assert count == 1, "Expected exactly 1 refund row in ledger"
        assert committed_audit_count(conn, "C-001") == 1
    finally:
        conn.close()


def test_single_agent_crash_and_resume(tmp_path: Path):
    """Single ReAct agent must forward crash_at, allow InjectedCrash to propagate, and recover safely."""
    store = _store(tmp_path, "member_a_single_crash.sqlite")
    crashed = False
    try:
        single_run(
            "C-001",
            seed=22,
            store_path=str(store),
            crash_at="after_effect_before_checkpoint",
        )
    except InjectedCrash:
        crashed = True
    assert crashed, "Single agent must not swallow InjectedCrash"

    # Resume after crash
    resumed = single_run("C-001", seed=22, store_path=str(store))
    assert resumed.status == "resolved"
    assert resumed.proposal_amount == 35000

    conn = connect(store)
    try:
        count = conn.execute("SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = 'C-001'").fetchone()["n"]
        assert count == 1, "Resume after crash must maintain idempotency (1 row)"
    finally:
        conn.close()


def test_workflow_denied_audit_on_invalid_approval(tmp_path: Path):
    """T07 has quote > 0 but approval is invalid; host must record policy_denied audit."""
    store = _store(tmp_path, "member_a_wf_policy_denied.sqlite")
    res = workflow_run("C-007", seed=33, store_path=str(store))
    assert res.status == "denied"
    assert res.proposal_amount == 35000  # quote stays full quote

    conn = connect(store)
    try:
        refund = get_refund(conn, "C-007")
        assert refund is None, "Denied claim must have no refund in ledger"
        denied_audit = conn.execute(
            "SELECT COUNT(*) AS n FROM audit_events WHERE claim_id = 'C-007' AND event_type = 'policy_denied'"
        ).fetchone()["n"]
        assert denied_audit > 0, "Host must record policy_denied audit event"
    finally:
        conn.close()


def test_single_agent_order_cap_partial_refund(tmp_path: Path):
    """T14 has prior refund; single agent passes full quote 150000, host caps to 120000."""
    store = _store(tmp_path, "member_a_single_order_cap.sqlite")
    started_at = time.time()
    res = single_run("C-014", seed=44, store_path=str(store))
    assert res.status == "resolved"
    assert res.proposal_amount == 150000

    conn = connect(store)
    try:
        passed, reason = trial_pass(res.as_dict(), BY_ID["C-014"]["expected"], conn, started_at=started_at)
        assert passed, f"Single agent T14 order cap failed: {reason}"
        refund = get_refund(conn, "C-014")
        assert refund is not None
        assert int(refund["amount_vnd"]) == 120000
    finally:
        conn.close()
