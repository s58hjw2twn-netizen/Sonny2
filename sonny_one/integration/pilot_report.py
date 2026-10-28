"""Deterministic human-readable report for evidence-gated pilot metrics."""
from __future__ import annotations

from sonny_one.integration.pilot_evaluation import TaskEvidence, scorecard


def render_pilot_report(tasks: list[TaskEvidence], *, pilot_label: str = "Pilot 002") -> str:
    if not isinstance(pilot_label, str) or not pilot_label.strip() or "\n" in pilot_label or "\r" in pilot_label:
        raise ValueError("invalid pilot label")
    data = scorecard(tasks)
    scored = data["verified_scored"]
    total = data["total_recorded"]
    rate = data["verified_success_rate"]
    status = "INSUFFICIENT EVIDENCE" if not scored else "DESCRIPTIVE RESULTS ONLY — NOT A PASS VERDICT"
    rate_text = "Not calculable" if rate is None else f"{rate:.1%} (verified scored tasks only)"
    return "\n".join([
        f"# {pilot_label} — Evidence Report",
        "",
        f"**Assessment:** {status}",
        f"**Tasks recorded:** {total}",
        f"**Verified and scored:** {scored}",
        f"**Verified successes:** {data['verified_successes']}",
        f"**Verified failures:** {data['verified_failures']}",
        f"**Unknown or unverified:** {data['unknown_or_unverified']}",
        f"**Verified success rate:** {rate_text}",
        f"**Corrections recorded:** {data['corrections_recorded']}",
        "",
        "## Interpretation",
        data["coverage_note"],
        "This report does not independently validate the supplied evidence,",
        "establish representativeness, or assign a passing grade.",
        "A pilot readiness verdict requires pre-registered criteria and review.",
    ])
