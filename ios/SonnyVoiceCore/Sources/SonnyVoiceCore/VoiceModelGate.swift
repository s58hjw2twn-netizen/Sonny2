import Foundation

/// Injectable inference boundary; the package does not bundle or download weights.
public protocol VoicePCMEngine: AnyObject {
    func start() throws
    func acceptMicrophonePCM(_ pcm16: Data) throws
    func cancelOutput()
    func stop()
}

public struct VoiceModelApproval {
    public let approved: Bool
    public let licenseReviewed: Bool
    public let locallyInstalled: Bool
    public let requiresExternalNetwork: Bool

    public init(approved: Bool, licenseReviewed: Bool, locallyInstalled: Bool,
                requiresExternalNetwork: Bool) {
        self.approved = approved
        self.licenseReviewed = licenseReviewed
        self.locallyInstalled = locallyInstalled
        self.requiresExternalNetwork = requiresExternalNetwork
    }
}

public enum VoiceModelError: Error, Equatable {
    case notApproved
    case notStarted
    case invalidMoshiFrame
}

/// Approval fields are policy inputs, not proof that a model is installed.
/// Caller must verify local artifacts and licenses independently.
public final class VoiceModelGate {
    private let engine: VoicePCMEngine
    private var started = false

    public init(engine: VoicePCMEngine, approval: VoiceModelApproval) throws {
        guard approval.approved && approval.licenseReviewed && approval.locallyInstalled
                && !approval.requiresExternalNetwork else { throw VoiceModelError.notApproved }
        self.engine = engine
    }

    public func start() throws {
        guard !started else { return }
        try engine.start()
        started = true
    }

    public func acceptMicrophonePCM(_ pcm16: Data) throws {
        guard started else { throw VoiceModelError.notStarted }
        try VoiceWire.validateFrame(pcm16)
        try engine.acceptMicrophonePCM(pcm16)
    }

    /// Moshi/Mimi consumes 80 ms of 24 kHz mono PCM16 per model input step.
    /// Reject partial and oversized frames before they reach the model adapter.
    public func acceptMoshiFrame(_ pcm16: Data) throws {
        guard pcm16.count == VoiceFrameAssembler.frameBytes else {
            throw VoiceModelError.invalidMoshiFrame
        }
        try acceptMicrophonePCM(pcm16)
    }

    public func cancelOutput() {
        if started { engine.cancelOutput() }
    }

    public func stop() {
        guard started else { return }
        started = false
        engine.cancelOutput()
        engine.stop()
    }
}
