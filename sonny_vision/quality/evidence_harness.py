"""Offline evidence-bundle evaluator for consented restoration experiments.

Reads JSON measurements only; never modifies images or makes an identity claim.
"""
import argparse
import hashlib
import json
from pathlib import Path
from sonny_vision.quality.review_pipeline import evaluate_restoration


def evaluate_bundle(bundle):
    if not isinstance(bundle, dict) or not isinstance(bundle.get("faces"), list):
        raise ValueError("bundle requires a faces list")
    result = evaluate_restoration(
        bundle["faces"],
        identity_scores=bundle.get("identity_scores"),
        reference_review_passed=bundle.get("reference_review_passed", False),
        owner_approved=bundle.get("owner_approved", False),
    )
    result["schema_version"] = 1
    result["automated_delivery_allowed"] = False
    return result


def evaluate_file(path):
    data = Path(path).read_bytes()
    bundle = json.loads(data)
    result = evaluate_bundle(bundle)
    result["evidence_sha256"] = hashlib.sha256(data).hexdigest()
    return result


def main():
    parser = argparse.ArgumentParser(description="Evaluate a local Sonny Vision JSON evidence bundle")
    parser.add_argument("bundle", help="Local JSON file containing measured facial evidence")
    args = parser.parse_args()
    print(json.dumps(evaluate_file(args.bundle), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
