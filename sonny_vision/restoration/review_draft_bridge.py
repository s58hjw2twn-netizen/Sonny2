"""Validate browser-exported review drafts without granting repair authorization.

This bridge NEVER signs decisions or sets reviewer_confirmed=True.
Only an independently authenticated approval service may do that.
"""
import hashlib
import json
from pathlib import Path


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_review_draft(source_path, proposal_path, draft_path):
    source_path, proposal_path, draft_path = map(Path,(source_path,proposal_path,draft_path))
    proposal=json.loads(proposal_path.read_text(encoding="utf-8"))
    draft=json.loads(draft_path.read_text(encoding="utf-8"))
    if not isinstance(proposal,dict) or not isinstance(draft,dict):
        raise ValueError("invalid JSON objects")
    source_hash=sha256(source_path)
    proposal_hash=sha256(proposal_path)
    if proposal.get("source_sha256")!=source_hash or draft.get("source_sha256")!=source_hash:
        raise ValueError("source fingerprint mismatch")
    if draft.get("proposal_sha256")!=proposal_hash:
        raise ValueError("proposal fingerprint mismatch")
    if draft.get("authorization_status")!="UNSIGNED_REVIEW_DRAFT":
        raise ValueError("expected an unsigned browser review draft")
    if draft.get("reviewer_confirmed") is not False:
        raise ValueError("browser draft must not claim authenticated confirmation")
    if "authorization_hmac_sha256" in draft:
        raise ValueError("browser draft must not contain an authorization signature")
    items=proposal.get("proposals")
    if not isinstance(items,list) or not items:
        raise ValueError("invalid proposal manifest")
    ids=[i.get("id") for i in items]
    if any(not isinstance(i,str) or not i for i in ids) or len(ids)!=len(set(ids)):
        raise ValueError("invalid or duplicate proposal IDs")
    votes=draft.get("decisions")
    if not isinstance(votes,list) or len(votes)!=len(ids):
        raise ValueError("every proposal must receive one decision")
    voted=[v.get("id") for v in votes]
    if len(voted)!=len(set(voted)) or set(voted)!=set(ids):
        raise ValueError("duplicate, unknown, or missing decisions")
    if any(v.get("decision") not in ("approve","reject") for v in votes):
        raise ValueError("invalid decision")
    return {"source_sha256":source_hash,"proposal_sha256":proposal_hash,
            "draft_sha256":sha256(draft_path),"candidate_count":len(ids),
            "approve_count":sum(v["decision"]=="approve" for v in votes),
            "reject_count":sum(v["decision"]=="reject" for v in votes),
            "reviewer_authenticated":False,"authorization_signed":False,
            "repair_permitted":False,"release_allowed":False}
