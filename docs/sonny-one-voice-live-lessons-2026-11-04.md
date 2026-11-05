# Sonny ONE Voice: streaming and verified-action contract

Status: engineering specification, NOT an implemented or tested voice system.
Scope: voice adapter only; preserve existing authentication, tool authorization, memory and GitHub branch protections.

## Design invariants
1. Microphone audio is streamed through a bounded, cancellable input queue. Never persist raw audio by default.
2. Voice activity detection distinguishes brief pauses from end-of-turn; thresholds are configurable and measured, not assumed.
3. User barge-in immediately stops playback, cancels queued speech, and invalidates the interrupted response's generation ID. No stale text/audio may resume after cancellation.
4. Stream partial text and audio as available. Display provisional text separately from confirmed tool results.
5. Speech recognition, reasoning, and speech synthesis are replaceable adapters. The default prototype must be usable with free local components; paid APIs require explicit opt-in and spending limits.
6. Tool calls require authenticated identity and existing per-action authorization. Speech never bypasses approval gates, even when a user interrupts or restates an instruction.
7. Spoken completion claims must be derived from verified tool results. Use explicit statuses: proposed, attempted, completed, independently verified, failed, and unknown.
8. No secrets, internal hidden tests, or private tool credentials enter model-generated speech or untrusted tool arguments.
9. Conversation memory is opt-in, provenance-tagged, scoped to the correct user/project, and subject to deletion controls.
10. Preserve existing behavior outside the voice adapter. Do not merge to main without explicit owner approval.

## Suggested event interface (proposal, not current API)
- input.audio.chunk(session_id, sequence, bytes)
- input.turn.final(session_id, turn_id)
- output.text.delta(turn_id, generation_id, text)
- output.audio.chunk(turn_id, generation_id, bytes)
- input.interrupt(session_id, generation_id)
- tool.result(turn_id, action_id, status, evidence_reference)
- output.completed(turn_id, generation_id)

Every emitted event must be scoped to an authenticated session. Reject out-of-order chunks and stale generation IDs. Treat interruption as cancellation, not permission to repeat actions.

## Independent acceptance tests (not yet run)
- Interrupt synthesized speech at 10%, 50%, and 90%; verify playback stops and no stale response resumes.
- Interrupt during a pending tool action; verify that cancellation does not accidentally duplicate or authorize the action.
- Test noise, silence, overlapping speech, and slow networks; record time-to-first-audio, time-to-useful-answer, and transcription error rate.
- Force tool failure, timeout, and authorization denial; verify spoken status never says 'completed'.
- Test two users and projects concurrently; verify no memory, audio, or tool-result cross-contamination.
- Disconnect/reconnect; verify bounded queues, cleanup, no credential leakage, and correct session resumption.
- Run existing repository regression tests and record commit, commands, exit codes, and CI links before claiming implementation success.

## Delivery gates
G0: verify actual branch tree, current voice code and CI.
G1: implement one adapter and unit tests on a feature branch.
G2: independent audio and authorization regression tests on HP Windows 11.
G3: private iPhone test with measured latency and interruption behavior.
G4: owner approval before merge, deployment, or paid service use.
