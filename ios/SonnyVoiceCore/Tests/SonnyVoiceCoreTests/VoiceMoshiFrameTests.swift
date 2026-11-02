import Foundation
import XCTest
@testable import SonnyVoiceCore

private final class MoshiFrameSpy: VoicePCMEngine {
    var accepted = 0
    func start() throws {}
    func acceptMicrophonePCM(_ pcm16: Data) throws { accepted += 1 }
    func cancelOutput() {}
    func stop() {}
}

final class VoiceMoshiFrameTests: XCTestCase {
    func testRequiresExactEightyMillisecondFrames() throws {
        let spy = MoshiFrameSpy()
        let gate = try VoiceModelGate(engine: spy, approval: VoiceModelApproval(
            approved: true, licenseReviewed: true, locallyInstalled: true, requiresExternalNetwork: false))
        let correct = Data(repeating: 0, count: VoiceFrameAssembler.frameBytes)
        XCTAssertThrowsError(try gate.acceptMoshiFrame(correct))
        try gate.start()
        XCTAssertThrowsError(try gate.acceptMoshiFrame(Data(repeating: 0, count: 3_838)))
        XCTAssertThrowsError(try gate.acceptMoshiFrame(Data(repeating: 0, count: 3_842)))
        XCTAssertThrowsError(try gate.acceptMoshiFrame(Data()))
        XCTAssertEqual(spy.accepted, 0)
        try gate.acceptMoshiFrame(correct)
        XCTAssertEqual(spy.accepted, 1)
        gate.stop()
        XCTAssertThrowsError(try gate.acceptMoshiFrame(correct))
        XCTAssertEqual(spy.accepted, 1)
    }
}
