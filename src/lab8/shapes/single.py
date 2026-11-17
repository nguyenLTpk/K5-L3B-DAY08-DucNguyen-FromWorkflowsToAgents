"""Shape B — one ReAct agent. Student work.

Use `lab8.runtime.run_react` with max_steps=8. `decide` may pick a read tool.
It must not call `issue_refund`. After the loop, the host validates the quote
and is the only writer.

A decide() that trusts ticket text over the order row will fail hidden claims
where the customer overstates the delay or cites a superseded clause.

Per-order cap: an order may already have been refunded by an earlier claim.
The read tool `lookup_refund_history` shows how much. The host still enforces
the cap, so pass the full quote to `durability.issue_refund`, not a net amount.

Caps: stop at 8 steps. Count model calls in the Budget so cost stays comparable.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.trace import Trace


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def _run(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    seed: int,
    crash_at: str | None,
) -> RunResult:
    budget = Budget()
    run_id = make_run_id("single", claim_id, seed)
    trace = Trace(run_id)

    step = 0

    def decide(seen: dict[str, Any]) -> dict[str, Any]:
        nonlocal step
        step += 1
        last_tool = seen.get("last_tool")

        # Step 0: Get claim view
        if last_tool is None:
            complete(budget, seed=seed, purpose="decide", prompt=f"get_claim_view {claim_id}")
            trace.add("thought", {"step": step, "intent": "get_claim_view", "claim_id": claim_id})
            return {"tool": "get_claim_view", "args": {"claim_id": claim_id}}

        # After get_claim_view
        if last_tool == "get_claim_view":
            claim_view = seen["last_result"]
            trace.add(
                "claim_view",
                {
                    "found": claim_view.get("found"),
                    "claim_id": claim_view.get("claim_id"),
                    "order_id": claim_view.get("order_id"),
                },
            )
            if not claim_view.get("found"):
                trace.add("decision", {"status": "failed", "reason": "unknown_claim"})
                return {"final": {"status": "failed", "proposal_amount": 0, "error_reason": "unknown_claim"}}

            if not claim_view.get("order_id"):
                trace.add("decision", {"status": "needs_info"})
                return {"final": {"status": "needs_info", "proposal_amount": 0, "error_reason": "missing_order_id"}}

            order_id = claim_view["order_id"]
            principal_id = claim_view["principal_id"]
            complete(budget, seed=seed, purpose="decide", prompt=f"lookup_order {order_id}")
            trace.add("thought", {"step": step, "intent": "lookup_order", "order_id": order_id})
            return {"tool": "lookup_order", "args": {"order_id": order_id, "principal_id": principal_id}}

        # After lookup_order
        if last_tool == "lookup_order":
            order_view = seen["last_result"]
            trace.add(
                "order_view",
                {
                    "visible": order_view.get("visible"),
                    "reason": order_view.get("reason"),
                    "order": order_view.get("order"),
                },
            )
            if not order_view.get("visible"):
                trace.add("decision", {"status": "escalated", "reason": order_view.get("reason")})
                return {"final": {"status": "escalated", "proposal_amount": 0, "error_reason": order_view.get("reason")}}

            order = order_view["order"]
            complete(budget, seed=seed, purpose="decide", prompt="compute_compensation")
            trace.add("thought", {"step": step, "intent": "compute_compensation"})
            return {"tool": "compute_compensation", "args": {"order": order}}

        # After compute_compensation
        if last_tool == "compute_compensation":
            quote_payload = seen["last_result"]
            proposal = int(quote_payload["amount_vnd"])
            trace.add("quote", quote_payload)
            complete(budget, seed=seed, purpose="draft", prompt=f"proposal={proposal}")
            if proposal <= 0:
                trace.add("decision", {"status": "denied", "reason": quote_payload.get("reason")})
                return {"final": {"status": "denied", "proposal_amount": 0, "error_reason": quote_payload.get("reason")}}

            trace.add("decision", {"status": "proceed_refund", "proposal_amount": proposal})
            return {"final": {"status": "proceed_refund", "proposal_amount": proposal}}

        # Fallback if unknown state
        return {"final": {"status": "failed", "proposal_amount": 0, "error_reason": "unexpected_step"}}

    react_result = run_react(
        conn,
        budget,
        observation={"claim_id": claim_id},
        decide=decide,
        max_steps=8,
        worker=False,
    )

    final = react_result.get("final") or {}
    status = final.get("status")

    if status == "proceed_refund":
        proposal = int(final["proposal_amount"])
        # TODO CP3: truyền crash_at vào durability.issue_refund, không bắt InjectedCrash.
        try:
            outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
        except InjectedCrash:
            trace.add("crash", {"at": crash_at})
            trace.write()
            raise

        if not outcome["ok"]:
            st = "failed" if outcome["conflict"] else "denied"
            return finish(
                conn,
                shape="single",
                claim_id=claim_id,
                seed=seed,
                status=st,
                proposal_amount=proposal,
                budget=budget,
                trace=trace,
                error_reason=outcome["reason"],
            )

        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status="resolved",
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=None,
        )

    return finish(
        conn,
        shape="single",
        claim_id=claim_id,
        seed=seed,
        status=status or "failed",
        proposal_amount=int(final.get("proposal_amount", 0)),
        budget=budget,
        trace=trace,
        error_reason=final.get("error_reason"),
    )
