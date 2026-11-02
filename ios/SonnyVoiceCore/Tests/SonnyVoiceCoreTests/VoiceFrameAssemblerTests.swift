import Foundation
import XCTest
@testable import SonnyVoiceCore

final class VoiceFrameAssemblerTests: XCTestCase {
    func testReframesIrregularInputWithoutDroppingOrDuplicatingSamples() throws {
        let assembler = VoiceFrameAssembler()
        let bytes = Data((0..<12_000).map { UInt8($0 % 251) })
        let inputLengths = [1_000, 4_800, 2_000, 4_200]
        var offset = 0
        var emitted: [Data] = []
        for length in inputLengths {
            emitted += try assembler.append(Data(bytes[offset..<(offset + length)]))
            offset += length
        }
        XCTAssertEqual(emitted.map(\.count), [3_840, 3_840, 3_840])
        XCTAssertEqual(Data(emitted.joined()), Data(bytes.prefix(11_520)))
        XCTAssertEqual(assembler.pendingBytes, 480)
    }

    func testInvalidInputDoesNotCorruptPendingAudio() throws {
        let assembler = VoiceFrameAssembler()
        XCTAssertTrue(try assembler.append(Data(repeating: 0x11, count: 200)).isEmpty)
        for invalid in [Data(), Data([0x11]), Data(repeating: 0x22, count: 4_802)] {
            XCTAssertThrowsError(try assembler.append(invalid))
            XCTAssertEqual(assembler.pendingBytes, 200)
        }
        let frames = try assembler.append(Data(repeating: 0x33, count: 3_640))
        XCTAssertEqual(frames.count, 1)
        XCTAssertEqual(frames[0], Data(repeating: 0x11, count: 200) + Data(repeating: 0x33, count: 3_640))
    }

    func testResetDiscardsPartialFrameAndNeverReplaysOldAudio() throws {
        let assembler = VoiceFrameAssembler()
        _ = try assembler.append(Data(repeating: 0x11, count: 3_838))
        assembler.reset()
        XCTAssertEqual(assembler.pendingBytes, 0)
        let frames = try assembler.append(Data(repeating: 0x22, count: 3_840))
        XCTAssertEqual(frames, [Data(repeating: 0x22, count: 3_840)])
    }

    func testMaxSizeFramesAreBounded() throws {
        let assembler = VoiceFrameAssembler()
        for _ in 0..<100 {
            let frames = try assembler.append(Data(repeating: 0x44, count: VoiceWire.maxFrameBytes))
            XCTAssertTrue(frames.allSatisfy { $0.count == VoiceFrameAssembler.frameBytes })
            XCTAssertLessThan(assembler.pendingBytes, VoiceFrameAssembler.frameBytes)
        }
        XCTAssertEqual(assembler.pendingBytes, 0)
    }
}
