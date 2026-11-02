# Sonny ONE Voice: upstream iOS audit (2026-11-02)

Source pinned: kyutai-labs/moshi-swift commit `df64ffdbe224e1ecb1ade1d254f347d379ed7f7a`.

Inspected exact upstream files:
- `Moshi/ContentView.swift`: `availableModels = [.hibiki, .asr]`. The iOS UI currently exposes Hibiki translation and ASR, **not** Moshi full-duplex conversation. Therefore compiling the app alone does not prove conversational Moshi works on iPhone.
- `Moshi/AudioRT.swift`: AVAudioEngine microphone capture and playback use mono 24 kHz Float32. Existing Sonny Python PCMFrame is **signed 16-bit PCM**, not wire-compatible with this float buffer without explicit conversion. Never pass Float32 bytes into the PCMFrame boundary.
- `Moshi/AudioRT.swift`: source warns that parts of microphone code may be macOS-specific and may not work on iOS. The code also contains an iOS conditional with a do/catch around commented-out code, requiring compilation verification.
- `README.md`: iOS app is experimental proof of concept; `make run-1b` builds/runs the **Mac CLI** target, not the iPhone app.
- `moshi.xcodeproj/project.pbxproj`: iOS deployment target 18.1, macOS 15.0.

## Revised no-cost milestone sequence
1. Run local Python voice boundary tests in an isolated environment and fix failures.
2. Add an iOS-specific AVAudioSession permission, capture, and output harness with an explicit 24kHz Float32 / signed-16-bit conversion contract, or use a native Float32 pipeline throughout.
3. Prove capture/playback on device before asserting on-device Moshi full duplex.
4. Expose a supported Moshi conversational model in a fork only after validating its actual model loading and memory budget.
5. Run a manual, cost-approved Xcode build and device test. A simulator compile is not an on-device inference test.

No user-facing iPhone audio, Moshi inference, or model memory performance has been verified.
