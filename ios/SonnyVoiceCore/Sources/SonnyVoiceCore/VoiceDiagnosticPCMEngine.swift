import Foundation

/// Deterministic, in-process diagnostic. It verifies that 80 ms microphone frames
/// reach the VoicePCMEngine boundary, but performs NO speech recognition,
/// synthesis, model inference, networking, or privileged assistant operations.
/// Confine calls to the same serialized executor as VoiceSessionController.
public final class VoiceDiagnosticPCMEngine: VoicePCMEngine {
    public private(set) var isRunning = false
    public private(set) var framesReceived = 0
    public private(set) var outputCancellations = 0

    public init() {}

    public func start() {
        framesReceived = 0
        isRunning = true
    }

    public func acceptMicrophonePCM(_ pcm16: Data) throws {
        guard isRunning else { throw VoiceModelError.notStarted }
        guard pcm16.count == VoiceFrameAssembler.frameBytes else {
            throw VoiceModelError.invalidMoshiFrame
        }
        framesReceived += 1
    }

    public func cancelOutput() { outputCancellations += 1 }

    public func stop() { isRunning = false }
}
