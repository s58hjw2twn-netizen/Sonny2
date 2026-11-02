# Sonny ONE Voice — implementation checkpoint (2026-11-02)

## Scope
This development branch contains a provider-neutral speech session state machine and a
fail-closed local engine registry. **No audio inference has been implemented or verified.**
No live Dessa, Moshi, or PersonaPlex weights have been downloaded or connected.

## Verified upstream sources
- Kyutai Moshi: https://github.com/kyutai-labs/moshi
  - Python/web client MIT; Rust backend Apache; model weights CC-BY 4.0.
  - Mimi streaming codec; Moshi two-stream speech framework.
- NVIDIA PersonaPlex: https://research.nvidia.com/labs/adlr/personaplex/
  - Code MIT; weights NVIDIA Open Model License; underlying Moshi CC-BY 4.0.
  - Check license conditions and attribution before distribution.

## Planned provider integration
1. Choose a pinned upstream release and review code, model licenses and dependencies.
2. Create a locally isolated adapter implementing start, stop, cancel_output.
3. Define authenticated bidirectional audio transport with strict size/rate limits.
4. Bind audio to an authenticated assistant session, never to privileged tools directly.
5. Add cancellation and microphone permission tests, including failure injection.
6. Benchmark real-device latency, barge-in, echo cancellation, and voice quality.
7. Gate public deployment and any paid inference on explicit owner approval.

## Security
- Do not transmit user audio to third parties by default.
- Do not expose GitHub tokens or model credentials to audio models.
- Do not treat transcribed speech as permission to merge, deploy, or spend money.
- Existing assistant authentication and research gates remain authoritative.

## Test status
New unit tests are committed but not yet executed in a verified runner.
