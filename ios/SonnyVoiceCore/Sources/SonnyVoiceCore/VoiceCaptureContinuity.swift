import Foundation

/// Tracks lost microphone input across the real-time callback and serial converter queue.
/// A lost buffer invalidates every queued buffer from the previous generation.
public final class VoiceCaptureContinuity: @unchecked Sendable {
    private let lock = NSLock()
    private var generation: UInt64 = 0

    public init() {}

    public func snapshot() -> UInt64 {
        lock.lock()
        defer { lock.unlock() }
        return generation
    }

    public func markDropped() {
        lock.lock()
        defer { lock.unlock() }
        // Exhaustion is terminal: never wrap to a previously valid generation.
        if generation < UInt64.max { generation += 1 }
    }

    public func isCurrent(_ value: UInt64) -> Bool {
        lock.lock()
        defer { lock.unlock() }
        return generation != UInt64.max && generation == value
    }
}

/// Serial-queue-only framing session. Never joins PCM samples across a capture gap.
public final class VoiceCaptureFramer {
    private let continuity: VoiceCaptureContinuity
    private let assembler = VoiceFrameAssembler()
    private var activeGeneration: UInt64?

    public init(continuity: VoiceCaptureContinuity) {
        self.continuity = continuity
    }

    public func append(_ pcm16: Data, generation: UInt64) throws -> [Data] {
        guard continuity.isCurrent(generation) else { return [] }
        if activeGeneration != generation {
            assembler.reset()
            activeGeneration = generation
        }
        let frames = try assembler.append(pcm16)
        return continuity.isCurrent(generation) ? frames : []
    }
}
