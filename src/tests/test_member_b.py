"""Tests authored by Member B for Shape C (orchestrator), handoff boundaries, and secret non-leakage.

Verifies:
- Handoff allowlist filtering (dropping parent secrets and forbidding write tools)
- Read-only investigator isolation (no write capabilities)
- Orchestrator trace security: no Canary secret / PII leakage
- Orchestrator durability: idempotency on replay, crash recovery, and order-cap handling
"""

import time
from pathlib import Path

# pyrefly: ignore[missing-import]
import pytest

from lab8.db import connect, init_store
from lab8.durability import InjectedCrash, committed_audit_count, get_refund
from lab8.handoff import HandoffError, make_handoff
from lab8.metrics import check_trace, trial_pass
from lab8.runtime import ToolRejected, dispatch
from lab8.schemas import Budget
from lab8.shapes.orchestrator import run_claim as orchestrator_run
from tests.conftest import BY_ID, CLAIMS, WORLD


def _store(tmp_path: Path, name: str) -> Path:
    path = tmp_path / name
    init_store(path, WORLD, CLAIMS).close()
    return path


def test_handoff_drops_secrets_and_forbids_write_tools():
    """make_handoff must drop unapproved fields and reject write tools."""
    dirty_facts = {
        "delay_days": 4,
        "carrier": "LOGIX_LOCAL",
        "parent_secret": "CANARY_SECRET_LEAK_TEST",
        "raw_headers": {"Authorization": "Bearer CANARY_SECRET_LEAK_TEST"},
    }
    handoff = make_handoff(
        request_id="REQ-TEST-B",
        claim_id="C-001",
        task="investigate",
        facts=dirty_facts,
        allowed_tools=["lookup_order", "lookup_policy"],
    )
    assert "parent_secret" not in handoff["facts"]
    assert "raw_headers" not in handoff["facts"]
    assert "CANARY_SECRET_" not in str(handoff)

    # Worker must not be granted write tools like issue_refund
    with pytest.raises(HandoffError):
        make_handoff(
            request_id="REQ-TEST-WRITE",
            claim_id="C-001",
            task="try_write",
            facts={},
            allowed_tools=["lookup_order", "issue_refund"],
        )


def test_investigator_tool_dispatch_rejects_mutations(tmp_path: Path):
    """Investigators dispatched as workers must reject host-only write tools."""
    store = _store(tmp_path, "member_b_investigator_dispatch.sqlite")
    conn = connect(store)
    budget = Budget()
    try:
        with pytest.raises(ToolRejected):
            dispatch(conn, budget, "issue_refund", {"claim_id": "C-001"}, worker=True)
        with pytest.raises(ToolRejected):
            dispatch(conn, budget, "append_audit", {"claim_id": "C-001"}, worker=True)
    finally:
        conn.close()


def test_orchestrator_trace_contract_and_no_canary_leak(tmp_path: Path):
    """Orchestrator run on C-010 must satisfy Trace contract v1 and not leak secrets/PII."""
    store = _store(tmp_path, "member_b_trace_security.sqlite")
    started_at = time.time()

    # C-010 contains CANARY_SECRET_PARENT_C-010, phone, and address in database row
    result_c010 = orchestrator_run("C-010", seed=11, store_path=str(store))
    trace_ok, trace_reason = check_trace(result_c010.as_dict(), started_at=started_at)
    assert trace_ok, f"Trace contract check failed: {trace_reason}"

    trace_file = Path(result_c010.trace_path)
    assert trace_file.is_file()
    trace_content = trace_file.read_text(encoding="utf-8")
    assert "CANARY_SECRET_PARENT_C-010" not in trace_content
    assert "0901000107" not in trace_content  # PII phone
    assert "12 Le Loi Q1" not in trace_content  # PII address

    # Verify pass with grader metrics
    conn = connect(store)
    try:
        passed, reason = trial_pass(
            result_c010.as_dict(), BY_ID["C-010"]["expected"], conn, started_at=started_at
        )
        assert passed, f"Trial pass failed for C-010: {reason}"
    finally:
        conn.close()


def test_orchestrator_idempotency_and_crash_recovery(tmp_path: Path):
    """Orchestrator must handle replay identically and recover from InjectedCrash safely."""
    # 1. Idempotency test (C-011)
    store_idem = _store(tmp_path, "member_b_orchestrator_idempotency.sqlite")
    first = orchestrator_run("C-011", seed=11, store_path=str(store_idem))
    second = orchestrator_run("C-011", seed=11, store_path=str(store_idem))
    assert first.status == "resolved"
    assert second.status == "resolved"
    assert first.proposal_amount == second.proposal_amount == 35000

    conn_idem = connect(store_idem)
    try:
        count = conn_idem.execute("SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = 'C-011'").fetchone()["n"]
        assert count == 1, "Idempotent replay must not create multiple ledger rows"
        assert committed_audit_count(conn_idem, "C-011") == 1
    finally:
        conn_idem.close()

    # 2. Crash & Resume test on fresh store (C-012)
    store_crash = _store(tmp_path, "member_b_orchestrator_crash.sqlite")
    crashed = False
    try:
        orchestrator_run(
            "C-012",
            seed=22,
            store_path=str(store_crash),
            crash_at="after_effect_before_checkpoint",
        )
    except InjectedCrash:
        crashed = True
    assert crashed, "Orchestrator must not swallow InjectedCrash"

    # Resume on the same database
    resumed = orchestrator_run("C-012", seed=22, store_path=str(store_crash))
    assert resumed.status == "resolved"
    assert resumed.proposal_amount == 35000

    conn_crash = connect(store_crash)
    try:
        effect = get_refund(conn_crash, "C-012")
        assert effect is not None
        assert int(effect["amount_vnd"]) == 35000
        assert committed_audit_count(conn_crash, "C-012") == 1
    finally:
        conn_crash.close()

