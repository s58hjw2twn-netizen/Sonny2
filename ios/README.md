# Sonny ONE Voice — native iPhone integration checkpoint

Pinned upstream source: `kyutai-labs/moshi-swift@df64ffdbe224e1ecb1ade1d254f347d379ed7f7a`.
Upstream `Moshi/ContentView.swift` exposes Hibiki and ASR in the iOS UI; this does **not** establish iPhone full-duplex Moshi inference.

- `SonnyVoiceCore` is a no-network Swift package for the existing Python `SV01` wire format, 24 kHz mono PCM16 conversion, and authenticated turn/interrupt generation checks.
- `SonnyVoiceApp/SonnyAudioIO.swift` is a native AVAudioEngine microphone/playback harness. It is not yet compiled or verified on iOS.
- `SonnyVoiceApp/SonnyVoiceDemoApp.swift` is a local-only device I/O demo. Its hardcoded `authenticated: true` is **only** for the offline test harness and MUST NOT be used as authentication for any assistant or network transport.
- `project.yml` is an XcodeGen project specification. It has not been generated or compiled on macOS.
- The host app must supply microphone permission text, establish authenticated encrypted transport, and connect a separately approved local or private model adapter. Never put model or GitHub credentials in the app.
- The in-process PCM callback is **not** a network transport. No audio leaves the device from this harness by itself.
- Microphone permission is requested explicitly; hardware audio is converted to 24 kHz mono PCM16 and reassembled into exact 80 ms (1,920-sample) Moshi-compatible frames. The portable assembler is tested for arbitrary chunk boundaries, malformed input, and reset; native iOS integration is still uncompiled.\n- Stale playback is rejected by turn epoch and queued output is dropped on interruption. A dropped microphone capture slot may still introduce an audio discontinuity; gap detection and on-device stress verification remain open.
- Route change and audio-session interruption stop capture/playback. Restart must be explicit.
- No model weights, network endpoint, iPhone build, device latency, echo cancellation, or natural conversation are verified.

## Verified locally on Linux

From `ios/SonnyVoiceCore`, run `swift test`. This verifies only portable Swift protocol tests, **not AVFoundation or device functionality**. Swift syntax parsing of the iOS sources is not a substitute for iOS typechecking.

## Next integration gate

On an owner-approved Mac with Xcode and XcodeGen installed, generate the project from `ios/project.yml`, compile the **Sonny Voice app itself** locally, and test microphone permission, captured frame count, speaker tone, and interruption on a physical iPhone. The manual macOS workflow now targets the Sonny app, not the upstream Moshi sample; it has not been dispatched and may consume billable minutes. Connect model inference only after audio I/O and interruption checks pass on device. No paid macOS CI is authorized.
