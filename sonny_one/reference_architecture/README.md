# Sonny ONE isolated offline reference
This is a small reference implementation, **not** the live Sonny ONE backend, a new language model, or production-ready software. It does not alter existing application entrypoints, CI, research baselines, or production behavior.

Run: `python -m unittest discover -s sonny_one/reference_architecture -p 'test_*.py' -v`

Includes a replaceable model protocol, deterministic offline demo, basic self-prediction recording, opt-in ephemeral memory, and input validation. No persistent memory, authentication, encryption, real LLM, animation, voice, deployment, or autonomous improvement. Do not use for sensitive data.

Next: inventory the existing application's inference call sites, adapt the contract to existing conventions, add error/timeout tests, then verify full CI before integration. Follow LOW_TOUCH_DEVELOPMENT.md and the frontier/independence charters.
