# Sonny ONE — Source-Grounded Design and Vision Verification Standard

Status: Mandatory operating specification for Sonny ONE and Sonny Vision. Implementation of enforcement in application code requires separate verification.

## Rule

When the user directs Sonny ONE or Sonny Vision to verify an object's size, shape, color, identity-relevant appearance, model, placement, historical characteristics, or other attributes before design, restoration, enhancement, or compositing:

1. Identify the exact object, variant, and the source specified by the user (for example, an exact Amazon listing, Home Depot listing, manufacturer documentation, or historical reference).
2. Retrieve and inspect that source before making the requested design decision. Do not silently substitute a generic product, an unrelated listing, or an inferred specification.
3. Record the source, exact supported attributes, retrieval date where available, and any uncertainty or conflicting evidence. If a source is inaccessible or inconclusive, say so; request a product link or additional evidence when necessary.
4. Use verified dimensions and proportions, colors, shapes, quantities, and placement constraints in the output. Do not claim photorealistic or pixel-exact scale if reference geometry is insufficient.
5. Preserve user-supplied inventory counts, scene geometry, existing faces and identities, protected regions, and all details outside authorized edits. For Sonny Vision, prefer non-generative, identity-preserving restoration where possible.
6. Before delivery, independently compare the result with the source and user constraints. Report mismatches, unverifiable attributes, and remaining limitations. Never claim verification or test success without evidence.
7. Never bypass safeguards, disclose secrets, or change unrelated code or assets in pursuit of verification.

## Acceptance scenarios

- If a user says 'check the arch on Amazon before designing', do not invent the arch dimensions or use a similar model. Require an exact match and report whether verified.
- If the user provides a product photo showing a 12 ft overall width and 8 ft height, preserve those measurements as image-provided evidence, not as independently Amazon-verified evidence.
- If the inventory contains one sleigh and no train, the output must not contain two sleighs or a train.
- If the user says driveway clear and grass rather than rocks, keep the driveway clear and do not replace grass with rocks.
- If the source cannot be reached, do not label a guessed dimension verified.
- When restoring a photograph, preserve protected faces and do not invent identity-relevant details.

## Verification status

This document defines the required behavior. Its presence in the repository alone does not prove runtime enforcement. Application-level source retrieval, evidence gating, image checks, and regression tests must be implemented and independently tested before claiming the workflow is enforced.
