# Sonny ONE Voice — live acceptance gates

This document is a checklist, **not** evidence that a live speech model or iPhone app works.

## Gate A — provider and licensing
- Record exact STT and TTS provider names, versions, model hashes, source URLs, and licenses.
- Obtain explicit owner approval for the provider, installation, any downloads, and any costs.
- Confirm actual runtime isolation externally (the Python approval flags do **not** enforce network restrictions).
- Verify the model is installed and usable; never set `installation_verified=True` based only on a planned install.

## Gate B — real speech inference
- Use a consented real recording with known transcript and supported 24 kHz mono PCM16 format.
- Run the speech probe with actual approved STT and TTS implementations, not fixture classes.
- Preserve model identifiers, input/output hashes, elapsed time, transcript, and human-reviewed accuracy.
- Check silence, noise, long utterances, wrong formats, malformed data, interrupted sessions, and provider failure.
- Never mark this gate complete from deterministic CI tests.

## Gate C — authenticated transport
- Verify actual transport peer authentication, TLS, replay prevention, bounded packet buffering,
  cancellation, reconnect, credential isolation, and server-side authorization.
- Confirm model output cannot directly execute privileged assistant tools.

## Gate D — iPhone beta
- Build/sign an actual iOS app with Xcode and a valid provisioning configuration.
- Install privately on an authorized device, obtain microphone permission, and verify audio routes.
- Test microphone-to-STT-to-response-to-TTS-to-speaker end to end, including barge-in and interruptions.
- Record device/iOS versions, reproducible steps, test evidence, failure logs, and owner acceptance.
- No public release or paid deployment without separate authorization.

## Current limitations
The portable Swift tests and syntax parse are **not** an iOS app build.
The speech provider boundary validates explicit flags; it does **not** sandbox code.
The engine probe can be run with fixtures; such runs do **not** establish real inference.
