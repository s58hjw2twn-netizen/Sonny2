# Sonny ONE — Model Access and Subscription Architecture
Status: adopted product direction, implementation pending
Date: 2026-10-15

## Development and launch
- Develop and test in ChatGPT for now; no standalone deployment required immediately.
- Eventually ship an independent Sonny ONE app with one customer-facing Sonny subscription.
- Preserve Sonny's memory, identity, policy, and audit layers independent of the underlying model provider.

## Model procurement
- Prefer appropriately licensed open-weight models, self-hosted inference, and commercially permitted free API tiers when quality, privacy, latency, and reliability are acceptable.
- Use paid provider APIs when they materially improve results or when free capacity is unavailable.
- Never scrape consumer chatbot interfaces, share consumer subscription credentials, or assume consumer chatbot plans include commercial API access.
- Verify provider licenses, retention/training terms, commercial usage permissions, quotas, and pricing before enabling a route.

## Intelligent routing contract
Inputs: task class, sensitivity, user consent, quality threshold, latency target, current provider health, per-request budget, monthly user budget.
Outputs: selected eligible model, estimated cost, reason code, fallback, auditable actual cost.
- Default to lowest total-cost eligible route meeting the quality floor, not simply the cheapest model.
- Sensitive requests may use only providers approved by the user or a suitable local model.
- Escalate to premium only within budget and permissions; require confirmation for exceptional charges.
- Enforce quotas, circuit breakers, retries, idempotency, caching where permitted, and provider-failure fallbacks.
- Never silently downgrade below the task quality/safety floor.

## Commercial unit economics
One Sonny subscription covers permitted provider inference costs. No separate third-party consumer subscriptions required.
Track variable inference, hosting/GPU, storage, search/tool, support, payment processing, refunds, and fraud/abuse costs.
Plan tiers and fair-use limits must be based on observed pilot usage and provider contracts, not guessed prices.
Track contribution margin by tier and user cohort; set hard monthly spend caps and alerts.
Disclose material plan limitations, provider data transfers, and premium usage rules.

## Research separation
Do not modify frozen SEB-1.0, CSAT-1.3, or RSI v1.3.
Do not connect experimental autonomous RSI to production billing or model procurement.
No production readiness claim until tests, security review, and legal/provider compliance review.
