import Foundation
import XCTest
@testable import SonnyVoiceCore

final class VoiceDiagnosticPCMEngineTests: XCTestCase {
    private let frame = Data(repeating: 0, count: VoiceFrameAssembler.frameBytes)

    func testDiagnosticConsumesExactMoshiFramesOnlyWhileRunning() throws {
        let engine = VoiceDiagnosticPCMEngine()
        XCTAssertThrowsError(try engine.acceptMicrophonePCM(frame))
        engine.start()
        XCTAssertThrowsError(try engine.acceptMicrophonePCM(Data(repeating: 0, count: 2)))
        XCTAssertEqual(engine.framesReceived, 0)
        try engine.acceptMicrophonePCM(frame)
        try engine.acceptMicrophonePCM(frame)
        XCTAssertEqual(engine.framesReceived, 2)
        engine.cancelOutput()
        XCTAssertEqual(engine.outputCancellations, 1)
        engine.stop()
        XCTAssertFalse(engine.isRunning)
        XCTAssertThrowsError(try engine.acceptMicrophonePCM(frame))
        engine.start()
        XCTAssertEqual(engine.framesReceived, 0)
    }

    func testGateRejectsUnauthenticatedAndStopsDiagnosticOnFailure() throws {
        let engine = VoiceDiagnosticPCMEngine()
        let model = try VoiceModelGate(engine: engine, approval: VoiceModelApproval(
            approved: true, licenseReviewed: true, locallyInstalled: true,
            requiresExternalNetwork: false))
        let session = VoiceSessionController(model: model, output: { _, _ in
            XCTFail("Diagnostic must never produce model audio")
        }, cancelPlayback: {})
        XCTAssertThrowsError(try session.start(authenticated: false))
        XCTAssertFalse(engine.isRunning)
        try session.start(authenticated: true)
        try session.acceptMicrophoneFrame(frame)
        XCTAssertEqual(engine.framesReceived, 1)
        session.stop()
        XCTAssertFalse(engine.isRunning)
        XCTAssertThrowsError(try session.acceptMicrophoneFrame(frame))
    }
}
