# Sonny Vision — Cross-Age Reference Fidelity Experiment

Status: PROPOSED / NOT IMPLEMENTED / NOT VALIDATED
Scope: research-only evaluation for Facial Identity Protection v2.

## Objective
Determine whether reference-guided restoration can preserve the subject's identity and apparent age in a historical target photo when reference photos were taken years or decades apart. Never treat visual plausibility as evidence of authentic reconstructed detail.

## Required inputs
- Permission-cleared original target image and, where available, authentic clean target-age ground truth.
- Verified same-person reference images, with approximate capture ages and provenance.
- Separately marked face, nonface, and damaged-region masks, independently reviewed.
- Fixed dataset manifest, hashes, model versions, random seeds, and licensing inventory.

## Baselines and comparisons
1. Unmodified source and existing conservative CLAHE restoration.
2. Conventional selective restoration without generative facial reconstruction.
3. Reference-guided methods in an isolated research environment, only after code, weights, and dependency rights are reviewed.
4. Compare same-age, older-reference, younger-reference, and no-reference cases. Repeat stochastic runs across fixed seeds.

## Evaluation
- Face landmark displacement normalized by interocular distance, including detector failure rate.
- Protected-region pixel differences, structural similarity, and mask leakage.
- Identity-embedding similarity only where a commercially authorized model is available; embeddings are supportive, not proof of identity.
- Apparent-age consistency and errors against known target age, with uncertainty and demographic limitations reported.
- Skin-texture changes: oversmoothing, ringing, hallucinated pores/wrinkles, and source/reference support.
- Human blinded review of identity, age, historical authenticity, and artifacts.
- Separate quality and identity metrics; quality gains cannot override failed preservation checks.
- Negative controls: deliberately alter eyes, nose, mouth, facial proportions, and apparent age to test whether gates catch them.

## Acceptance gate
- Define thresholds on a held-out permission-cleared validation set before reporting results.
- Report per-case failures, false accept/reject rates, uncertainty, and performance by reference age gap.
- No automatic replacement of original facial pixels; no customer delivery without explicit review and approval.
- Keep original files immutable; record hashes and restoration provenance.
- Commercial integration blocked until code, weights, datasets, and dependencies have documented permissions.

## Research candidate
MeInTime: https://github.com/teer4/MeInTime
Paper: https://arxiv.org/abs/2603.18645
Candidate only: checkpoint availability, exact licensing, reproducibility, and performance are not verified here.

## Next engineering actions
1. Verify existing archival-engine compilation and regression tests.
2. Implement a model-independent benchmark harness and deliberate-distortion negative controls.
3. Add cross-age evaluation fixtures with consent and provenance.
4. Only then run isolated reference-guided comparisons; publish measured results before considering adoption.
