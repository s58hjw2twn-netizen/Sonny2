import Foundation
import XCTest
@testable import SonnyVoiceCore

final class VoiceCaptureContinuityTests: XCTestCase {
    func testDroppedInputInvalidatesQueuedSamples() throws {
        let continuity = VoiceCaptureContinuity()
        let framer = VoiceCaptureFramer(continuity: continuity)
        let original = continuity.snapshot()
        XCTAssertEqual(try framer.append(Data(repeating: 0x11, count: 1_920), generation: original).count, 0)
        continuity.markDropped()
        XCTAssertFalse(continuity.isCurrent(original))
        XCTAssertTrue(try framer.append(Data(repeating: 0x22, count: 1_920), generation: original).isEmpty)
        let current = continuity.snapshot()
        XCTAssertTrue(try framer.append(Data(repeating: 0x33, count: 1_920), generation: current).isEmpty)
        let completed = try framer.append(Data(repeating: 0x44, count: 1_920), generation: current)
        XCTAssertEqual(completed.count, 1)
        XCTAssertEqual(completed[0], Data(repeating: 0x33, count: 1_920) + Data(repeating: 0x44, count: 1_920))
    }

    func testMultipleDropsAndMalformedFrames() throws {
        let continuity = VoiceCaptureContinuity()
        let framer = VoiceCaptureFramer(continuity: continuity)
        let stale = continuity.snapshot()
        continuity.markDropped()
        continuity.markDropped()
        XCTAssertFalse(continuity.isCurrent(stale))
        let current = continuity.snapshot()
        XCTAssertThrowsError(try framer.append(Data([0x01]), generation: current))
        XCTAssertTrue(try framer.append(Data(repeating: 0x55, count: 3_840), generation: current).count == 1)
    }

    func testConcurrentDiscontinuityMarksAreNotLost() {
        let continuity = VoiceCaptureContinuity()
        let initial = continuity.snapshot()
        DispatchQueue.concurrentPerform(iterations: 128) { _ in continuity.markDropped() }
        XCTAssertEqual(continuity.snapshot(), initial + 128)
        XCTAssertFalse(continuity.isCurrent(initial))
    }
}
