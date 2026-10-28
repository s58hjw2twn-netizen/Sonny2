# Tool Authorization Gate (research prototype)

The trusted caller must invoke `execute_authorized` **before** any tool call.
For exact localized image edits, a full-image generator is rejected because
it cannot guarantee unchanged pixels outside the allowed mask.

The gate checks explicit method allowlists, repeated failures, presence of a
reference identifier, and declared tool capabilities. Capability declarations
and reference identifiers are **not independently authenticated**. Production
requires a trusted capability registry, source verification, isolated tool
execution, mandatory post-edit pixel comparison and an artifact-bound customer
approval. A caller that bypasses this function is not protected.

This gate does **not** alter ChatGPT's built-in image-generation tool or
enforce rules on any tools outside an integrated trusted orchestrator.

Run: `python -m unittest discover -s tests -p 'test_vision_*.py'`
