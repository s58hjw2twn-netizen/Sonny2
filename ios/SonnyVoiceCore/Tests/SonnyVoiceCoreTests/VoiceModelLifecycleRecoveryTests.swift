import Foundation
import XCTest
@testable import SonnyVoiceCore

private enum GateEngineFailure: Error { case startup, inference }

private final class GateLifecycleSpy: VoicePCMEngine {
    var starts = 0
    var inputs = 0
    var cancels = 0
    var stops = 0
    var failStart = false
    var failInput = false

    func start() throws {
        starts += 1
        if failStart { throw GateEngineFailure.startup }
    }
    func acceptMicrophonePCM(_ pcm16: Data) throws {
        inputs += 1
        if failInput { throw GateEngineFailure.inference }
    }
    func cancelOutput() { cancels += 1 }
    func stop() { stops += 1 }
}

final class VoiceModelLifecycleRecoveryTests: XCTestCase {
    private func approved(_ engine: GateLifecycleSpy) throws -> VoiceModelGate {
        try VoiceModelGate(engine: engine, approval: VoiceModelApproval(
            approved: true, licenseReviewed: true, locallyInstalled: true,
            requiresExternalNetwork: false))
    }

    func testFailedStartCleansPartialResourcesAndAllowsExplicitRetry() throws {
        let engine = GateLifecycleSpy()
        engine.failStart = true
        let gate = try approved(engine)
        XCTAssertThrowsError(try gate.start())
        XCTAssertEqual(engine.starts, 1)
        XCTAssertEqual(engine.cancels, 1)
        XCTAssertEqual(engine.stops, 1)
        XCTAssertThrowsError(try gate.acceptMoshiFrame(Data(repeating: 0, count: 3_840)))
        XCTAssertEqual(engine.inputs, 0)

        engine.failStart = false
        try gate.start()
        try gate.acceptMoshiFrame(Data(repeating: 0, count: 3_840))
        XCTAssertEqual(engine.starts, 2)
        XCTAssertEqual(engine.inputs, 1)
        gate.stop()
        XCTAssertEqual(engine.stops, 2)
        gate.stop()
        XCTAssertEqual(engine.stops, 2)
    }

    func testInferenceFailureStopsOnceAndRejectsSubsequentInput() throws {
        let engine = GateLifecycleSpy()
        let gate = try approved(engine)
        try gate.start()
        engine.failInput = true
        XCTAssertThrowsError(try gate.acceptMoshiFrame(Data(repeating: 0, count: 3_840)))
        XCTAssertEqual(engine.cancels, 1)
        XCTAssertEqual(engine.stops, 1)
        XCTAssertThrowsError(try gate.acceptMoshiFrame(Data(repeating: 0, count: 3_840)))
        XCTAssertEqual(engine.inputs, 1)
        gate.stop()
        XCTAssertEqual(engine.stops, 1)
    }

    func testNetworkDependentOrUnreviewedModelsAreDeniedBeforeStart() throws {
        let engine = GateLifecycleSpy()
        let approvals = [
            VoiceModelApproval(approved: true, licenseReviewed: true,
                               locallyInstalled: true, requiresExternalNetwork: true),
            VoiceModelApproval(approved: true, licenseReviewed: false,
                               locallyInstalled: true, requiresExternalNetwork: false),
            VoiceModelApproval(approved: true, licenseReviewed: true,
                               locallyInstalled: false, requiresExternalNetwork: false),
            VoiceModelApproval(approved: false, licenseReviewed: true,
                               locallyInstalled: true, requiresExternalNetwork: false)
        ]
        for approval in approvals {
            XCTAssertThrowsError(try VoiceModelGate(engine: engine, approval: approval))
        }
        XCTAssertEqual(engine.starts, 0)
    }
}
