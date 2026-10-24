"""Read-only application readiness checks for Sonny ONE.

These checks deliberately distinguish a functioning local demo from a secure,
commercially deployable AI assistant. No network, secrets or external actions.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class ProductReadiness:
    local_chat_demo: bool
    responsive_browser_shell: bool
    explicit_sample_memory: bool
    authenticated_private_route: bool
    hosted_model_verified: bool
    durable_encrypted_memory_verified: bool
    real_iphone_safari_verified: bool
    production_security_review_passed: bool

    def report(self) -> dict:
        data = asdict(self)
        required = (
            "hosted_model_verified",
            "durable_encrypted_memory_verified",
            "real_iphone_safari_verified",
            "production_security_review_passed",
        )
        return {
            "capabilities": data,
            "production_ready": all(data[k] for k in required),
            "missing_release_gates": [k for k in required if not data[k]],
            "automatic_deployment_allowed": False,
            "research_promotion_allowed": False,
        }


def current_verified_baseline() -> ProductReadiness:
    """Conservative code-inspection baseline; not a live deployment attestation."""
    return ProductReadiness(
        local_chat_demo=True,
        responsive_browser_shell=True,
        explicit_sample_memory=True,
        authenticated_private_route=True,
        hosted_model_verified=False,
        durable_encrypted_memory_verified=False,
        real_iphone_safari_verified=False,
        production_security_review_passed=False,
    )
