import Foundation
import XCTest
@testable import SonnyVoiceCore

final class VoiceWireTests: XCTestCase {
    func testPCM16Compatibility() throws {
        let pcm = try VoiceWire.pcm16(from: [-1, 0, 1])
        XCTAssertEqual([UInt8](pcm), [0, 128, 0, 0, 255, 127])
        XCTAssertEqual(try VoiceWire.floats(from: pcm), [-1, 0, Float(32767.0 / 32768.0)])
    }

    func testClippingAndInvalidFrames() throws {
        XCTAssertEqual(try VoiceWire.pcm16(from: [-5, 5]), Data([0, 128, 255, 127]))
        XCTAssertThrowsError(try VoiceWire.pcm16(from: []))
        XCTAssertThrowsError(try VoiceWire.pcm16(from: [Float.nan]))
        XCTAssertThrowsError(try VoiceWire.pcm16(from: [Float.infinity]))
        XCTAssertThrowsError(try VoiceWire.pcm16(from: Array(repeating: 0, count: 2401)))
        XCTAssertThrowsError(try VoiceWire.floats(from: Data([0])))
    }

    func testPythonCompatiblePacketAndReplayProtection() throws {
        let pcm = Data([0, 128, 255, 127])
        let packet = try VoiceWire.encode(sequence: 0, pcm16: pcm)
        XCTAssertEqual([UInt8](packet.prefix(16)), [83, 86, 48, 49, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4])
        let decoder = VoiceWireDecoder()
        XCTAssertEqual(try decoder.decode(packet), pcm)
        XCTAssertThrowsError(try decoder.decode(packet))
        XCTAssertEqual(try decoder.decode(VoiceWire.encode(sequence: 1, pcm16: pcm)), pcm)
    }

    func testMalformedPacketsDoNotConsumeSequence() throws {
        let good = try VoiceWire.encode(sequence: 0, pcm16: Data([0, 0]))
        let decoder = VoiceWireDecoder()
        XCTAssertThrowsError(try decoder.decode(Data()))
        XCTAssertThrowsError(try decoder.decode(Data(good.dropLast())))
        var badMagic = good
        badMagic[0] = 0
        XCTAssertThrowsError(try decoder.decode(badMagic))
        XCTAssertThrowsError(try decoder.decode(try VoiceWire.encode(sequence: 2, pcm16: Data([0, 0]))))
        XCTAssertEqual(try decoder.decode(good), Data([0, 0]))
        decoder.close()
        XCTAssertThrowsError(try decoder.decode(try VoiceWire.encode(sequence: 1, pcm16: Data([0, 0]))))
    }
}
