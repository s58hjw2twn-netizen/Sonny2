import Foundation
import XCTest
@testable import SonnyVoiceCore

private final class ReentrantEngineSpy: VoicePCMEngine {
    var stopCount = 0
    func start() throws {}
    func acceptMicrophonePCM(_ pcm16: Data) throws {}
    func cancelOutput() {}
    func stop() { stopCount += 1 }
}

final class VoiceReentrantPlaybackTests: XCTestCase {
    func testSynchronousStopInsideFinalPlaybackCannotResurrectOutputEpoch() throws {
        let engine = ReentrantEngineSpy()
        let gate = try VoiceModelGate(engine: engine, approval: VoiceModelApproval(
            approved: true, licenseReviewed: true, locallyInstalled: true, requiresExternalNetwork: false))
        var session: VoiceSessionController!
        var callbacks = 0
        session = VoiceSessionController(model: gate,
            output: { _, _ in XCTFail("Legacy output must not run") },
            streamingOutput: { _, _, isFinal in
                XCTAssertTrue(isFinal)
                callbacks += 1
                session.stop()
            },
            cancelPlayback: {})
        try session.start(authenticated: true)
        let epoch = try session.beginModelOutput()
        XCTAssertThrowsError(try session.deliverModelOutput(
            Data(repeating: 0, count: 3_840), epoch: epoch, isFinalFrame: true)) { error in
            XCTAssertEqual(error as? VoiceSessionError, .staleOutput)
        }
        XCTAssertEqual(session.state, .idle)
        XCTAssertEqual(callbacks, 1)
        XCTAssertThrowsError(try session.finishModelOutput(epoch: epoch))
        XCTAssertThrowsError(try session.deliverModelOutput(
            Data(repeating: 0, count: 3_840), epoch: epoch, isFinalFrame: true))
        XCTAssertEqual(callbacks, 1)
        XCTAssertEqual(engine.stopCount, 1)
    }
}
