import Foundation

/// Reframes 24 kHz mono PCM16 input into the 80 ms / 1,920-sample chunks
/// used by Moshi/Mimi. Not a model adapter or an authenticated transport.
/// Confine each instance to one serial capture queue and reset it on discontinuity.
public final class VoiceFrameAssembler {
    public static let frameSamples = 1_920
    public static let frameBytes = frameSamples * 2
    private var remainder = Data()

    public init() {}

    public var pendingBytes: Int { remainder.count }

    /// Input follows the bounded SV01 PCM frame contract; output is always
    /// exactly one 80 ms frame. Invalid input never modifies buffered samples.
    public func append(_ pcm16: Data) throws -> [Data] {
        try VoiceWire.validateFrame(pcm16)
        remainder.append(pcm16)
        var frames: [Data] = []
        while remainder.count >= Self.frameBytes {
            frames.append(Data(remainder.prefix(Self.frameBytes)))
            remainder.removeFirst(Self.frameBytes)
        }
        return frames
    }

    /// Drop incomplete audio when stopping, restarting, or losing input frames.
    public func reset() { remainder.removeAll(keepingCapacity: true) }
}
