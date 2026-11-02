import Foundation
import XCTest
@testable import SonnyVoiceCore

private enum FakeEngineError: Error { case startup, inference }

private final class FakeVoiceEngine: VoicePCMEngine {
    var started = 0
    var received = 0
    var cancelled = 0
    var stopped = 0
    var failStart = false
    var failInput = false
    func start() throws {
        started += 1
        if failStart { throw FakeEngineError.startup }
    }
    func acceptMicrophonePCM(_ pcm16: Data) throws {
        received += 1
        if failInput { throw FakeEngineError.inference }
    }
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

    func testFailedStartupReleasesResourcesBeforeRetry() throws {
        let engine = FakeVoiceEngine()
        engine.failStart = true
        let gate = try VoiceModelGate(engine: engine, approval: VoiceModelApproval(
            approved: true, licenseReviewed: true, locallyInstalled: true, requiresExternalNetwork: false))
        XCTAssertThrowsError(try gate.start())
        XCTAssertEqual(engine.cancelled, 1)
        XCTAssertEqual(engine.stopped, 1)
        XCTAssertThrowsError(try gate.acceptMoshiFrame(Data(repeating: 0, count: 3_840)))
        engine.failStart = false
        try gate.start()
        gate.stop()
        XCTAssertEqual(engine.started, 2)
        XCTAssertEqual(engine.stopped, 2)
    }

    func testInferenceFailureClosesGateAndRejectsFurtherInput() throws {
        let engine = FakeVoiceEngine()
        engine.failInput = true
        let gate = try VoiceModelGate(engine: engine, approval: VoiceModelApproval(
            approved: true, licenseReviewed: true, locallyInstalled: true, requiresExternalNetwork: false))
        try gate.start()
        let frame = Data(repeating: 0, count: 3_840)
        XCTAssertThrowsError(try gate.acceptMoshiFrame(frame))
        XCTAssertEqual(engine.cancelled, 1)
        XCTAssertEqual(engine.stopped, 1)
        XCTAssertThrowsError(try gate.acceptMoshiFrame(frame))
        XCTAssertEqual(engine.received, 1)
        gate.stop() // Terminal cleanup must be idempotent.
        XCTAssertEqual(engine.stopped, 1)
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
