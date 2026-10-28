# Sonny Vision precision restoration release policy

1. Preserve the original source and its SHA-256 fingerprint.
2. Explicitly approve a small editing mask and authorize only a pixel-locked compositor.
3. Require an independently authenticated reference for historical or identity-sensitive corrections.
4. Compare source and candidate pixel by pixel; reject any outside-mask changes.
5. Require independent inspection for orientation, historical correctness, and blending artifacts.
6. Record an audit containing source, candidate and mask hashes, reference, reviewer, and changed-pixel count.
7. Do not release the final image without explicit customer approval. A watermarked preview is a separate step to implement and test.

The current code provides a fail-closed verification function, not a trusted authentication service or production approval UI. A caller must use the gate; it does not control external image-generation tools. A string reviewer ID alone is not independently authenticated. Do not equate a passing pixel test with historical accuracy or full end-to-end validation.
