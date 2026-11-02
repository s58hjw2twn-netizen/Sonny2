import Foundation

/// Wire format shared with sonny_one.voice_packet and sonny_one.voice_stream.
/// The enclosing transport MUST authenticate its peer and provide encryption.
public enum VoiceWireError: Error, Equatable {
    case invalidFrame
    case invalidPacket
    case unexpectedSequence
    case closed
}

public enum VoiceWire {
    public static let sampleRate = 24_000
    public static let maxFrameBytes = 4_800 // 100 ms of mono, signed PCM16
    public static let headerBytes = 16 // "SV01" + network-order UInt64 + UInt32

    public static func pcm16(from samples: [Float]) throws -> Data {
        guard !samples.isEmpty && samples.count <= maxFrameBytes / 2 else {
            throw VoiceWireError.invalidFrame
        }
        var data = Data(capacity: samples.count * 2)
        for sample in samples {
            guard sample.isFinite else { throw VoiceWireError.invalidFrame }
            let scaled = (Double(max(-1, min(1, sample))) * 32768).rounded(.toNearestOrEven)
            let value = Int16(max(-32768, min(32767, Int(scaled))))
            let bits = UInt16(bitPattern: value)
            data.append(UInt8(truncatingIfNeeded: bits))
            data.append(UInt8(truncatingIfNeeded: bits >> 8))
        }
        return data
    }

    public static func floats(from pcm16: Data) throws -> [Float] {
        try validateFrame(pcm16)
        let bytes = [UInt8](pcm16)
        return stride(from: 0, to: bytes.count, by: 2).map { i in
            let bits = UInt16(bytes[i]) | (UInt16(bytes[i + 1]) << 8)
            return Float(Int16(bitPattern: bits)) / 32768
        }
    }

    public static func validateFrame(_ data: Data) throws {
        guard !data.isEmpty && data.count.isMultiple(of: 2) && data.count <= maxFrameBytes else {
            throw VoiceWireError.invalidFrame
        }
    }

    public static func encode(sequence: UInt64, pcm16: Data) throws -> Data {
        try validateFrame(pcm16)
        var packet = Data([0x53, 0x56, 0x30, 0x31])
        for shift in stride(from: 56, through: 0, by: -8) {
            packet.append(UInt8(truncatingIfNeeded: sequence >> shift))
        }
        let length = UInt32(pcm16.count)
        for shift in stride(from: 24, through: 0, by: -8) {
            packet.append(UInt8(truncatingIfNeeded: length >> shift))
        }
        packet.append(pcm16)
        return packet
    }
}

/// One decoder per authenticated channel. Sequence numbers never reset mid-channel.
public final class VoiceWireDecoder {
    private var expected: UInt64 = 0
    private var isClosed = false

    public init() {}

    public func decode(_ packet: Data) throws -> Data {
        if isClosed { throw VoiceWireError.closed }
        guard packet.count >= VoiceWire.headerBytes,
              packet.count <= VoiceWire.headerBytes + VoiceWire.maxFrameBytes else {
            throw VoiceWireError.invalidPacket
        }
        let bytes = [UInt8](packet)
        guard bytes[0...3].elementsEqual([0x53, 0x56, 0x30, 0x31]) else {
            throw VoiceWireError.invalidPacket
        }
        var sequence: UInt64 = 0
        for byte in bytes[4..<12] { sequence = (sequence << 8) | UInt64(byte) }
        var length: UInt32 = 0
        for byte in bytes[12..<16] { length = (length << 8) | UInt32(byte) }
        guard Int(length) == packet.count - VoiceWire.headerBytes else {
            throw VoiceWireError.invalidPacket
        }
        let payload = Data(bytes[VoiceWire.headerBytes...])
        try VoiceWire.validateFrame(payload)
        guard sequence == expected else { throw VoiceWireError.unexpectedSequence }
        // Fail closed at UInt64 exhaustion rather than permitting replay on wraparound.
        guard expected != UInt64.max else { throw VoiceWireError.unexpectedSequence }
        expected += 1
        return payload
    }

    public func close() { isClosed = true }
}
