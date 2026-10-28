"""Custody-checked APL self-prediction evidence, read-only.

A valid custodian MAC authenticates the supplied record relative to the key
holder. It does not establish preregistration, independence, or factual truth.
The key must be supplied outside source control.
"""
from __future__ import annotations

from sonny_one.apl.custody import verify_evidence
from sonny_one.causal_apl_bridge import apl_self_prediction_report


def custody_checked_apl_report(records, envelope, *, custodian_key: bytes,
                               custodian_id: str) -> dict:
    if not isinstance(records, list) or not records:
        raise ValueError("nonempty records required")
    sealed_record = {"records": records}
    if not verify_evidence(sealed_record, envelope, custodian_key,
                           expected_custodian=custodian_id):
        raise PermissionError("custody envelope verification failed")
    result = apl_self_prediction_report(records)
    result["custody_mac_verified"] = True
    result["custodian_id"] = custodian_id
    result["preregistration_verified"] = False
    result["independent_grading_verified"] = False
    result["provenance_verified"] = False
    return result
