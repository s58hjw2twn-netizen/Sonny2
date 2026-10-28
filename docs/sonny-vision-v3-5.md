# Sonny Vision v3.5: release gate (experimental)

The new `restoration_release_gate` combines separately supplied per-face
geometry and identity measurements with texture review, reference review, and
explicit owner approval. It fails closed for absent or failing evidence.

The default identity-score threshold (0.80) is **provisional and uncalibrated**.
Scores must be normalized to [0,1] by the caller; do not assume cosine similarity
is calibrated or interchangeable across models. A passing gate is a workflow
decision, not proof of biometric identity.

No face detector, embedding model, pretrained weights, image processor, or
commercially restricted dependencies are included. No automated delivery is
authorized. Benchmark on consented reference images before any commercial use.
