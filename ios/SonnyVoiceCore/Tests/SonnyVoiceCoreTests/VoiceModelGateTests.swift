import Foundation
import XCTest
@testable import SonnyVoiceCore

private final class FakeVoiceEngine: VoicePCMEngine {
    var started = 0
    var received = 0
    var cancelled = 0
    var stopped = 0
    func start() throws { started += 1 }
    func acceptMicrophonePCM(_ pcm16: Data) throws { received += 1 }
    func cancelOutput() { cancelled += 1 }
    func stop() { stopped += 1 }
}

final class VoiceModelGateTests: XCTestCase {
    func testRejectsUnapprovedAndNetworkModels() throws {
        let engine = FakeVoiceEngine()
        for approval in [
            VoiceModelApproval(approved: false, licenseReviewed: true, locallyInstalled: true, requiresExternalNetwork: false),
            VoiceModelApproval(approved: true, licenseReviewed: false, locallyInstalled: true, requiresExternalNetwork: false),
            VoiceModelApproval(approved: true, licenseReviewed: true, locallyInstalled: false, requiresExternalNetwork: false),
            VoiceModelApproval(approved: true, licenseReviewed: true, locallyInstalled: true, requiresExternalNetwork: true),
        ] {
            XCTAssertThrowsError(try VoiceModelGate(engine: engine, approval: approval))
        }
        XCTAssertEqual(engine.started, 0)
    }

    func testBoundedInputAndCancellation() throws {
        let engine = FakeVoiceEngine()
        let gate = try VoiceModelGate(engine: engine, approval: VoiceModelApproval(
            approved: true, licenseReviewed: true, locallyInstalled: true, requiresExternalNetwork: false))
        XCTAssertThrowsError(try gate.acceptMicrophonePCM(Data([0, 0])))
        try gate.start()
        XCTAssertThrowsError(try gate.acceptMicrophonePCM(Data([0])))
        try gate.acceptMicrophonePCM(Data([0, 0]))
        XCTAssertEqual(engine.received, 1)
        gate.cancelOutput()
        gate.stop()
        XCTAssertEqual(engine.cancelled, 2)
        XCTAssertEqual(engine.stopped, 1)
        XCTAssertThrowsError(try gate.acceptMicrophonePCM(Data([0, 0])))
    }
}
