"""Read-only score attachment with experiment identity validation.

External grader reports are separate evidence. They never modify the runner's
status, lineage hash, or human-approval boundary.
"""
import json
from pathlib import Path
from .metrics import compare_metrics


def attach_scores(evaluation: dict, evidence: dict) -> dict:
    if not isinstance(evaluation, dict) or not isinstance(evidence, dict):
        raise ValueError("Evaluation and evidence must be objects")
    required = ("candidate_id", "base_revision", "trusted_suite_sha256",
                "heldout_suite_sha256", "image")
    for key in required:
        if not isinstance(evaluation.get(key), str) or not evaluation[key]:
            raise ValueError(f"Evaluation missing {key}")
        if evidence.get(key) != evaluation[key]:
            raise ValueError(f"Evidence mismatch: {key}")
    if evidence.get("grader") in (None, "") or not isinstance(evidence["grader"], str):
        raise ValueError("Independent grader identifier required")
    if evidence.get("grader") == "candidate":
        raise ValueError("Candidate cannot self-certify scores")
    metrics = compare_metrics(evidence.get("baseline_scores"),
                              evidence.get("candidate_scores"))
    return {
        "candidate_id": evaluation["candidate_id"],
        "base_revision": evaluation["base_revision"],
        "lineage_hash": evaluation.get("lineage_hash"),
        "grader": evidence["grader"],
        "metrics": metrics,
        "runner_status": evaluation.get("status"),
        "promotion": "FORBIDDEN",
        "improvement_proven": False,
        "note": "External score attachment only; no automatic eligibility or promotion."
    }



def attach_scores_verified(evaluation: dict, evidence: dict, ledger) -> dict:
    """Require local report/ledger agreement before score attachment.

    Ledger integrity does not authenticate external grader identity or custody.
    """
    from .provenance import verify_report_lineage
    if not verify_report_lineage(evaluation, ledger):
        raise ValueError("Evaluation report is not bound to a valid ledger entry")
    attached = attach_scores(evaluation, evidence)
    attached["local_lineage_verified"] = True
    attached["note"] = ("Report agrees with local hash-linked ledger. "
                        "Independent grader custody and scores remain unverified.")
    return attached


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True,
                        help="Required hash-linked experiment ledger")
    args = parser.parse_args()
    print(json.dumps(attach_scores_verified(json.loads(args.evaluation.read_text()),
                                            json.loads(args.evidence.read_text()),
                                            args.ledger), indent=2))


if __name__ == "__main__":
    main()
