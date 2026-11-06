import Foundation
import XCTest
@testable import SonnyVoiceCore

private enum SessionEngineFailure: Error { case unavailable, inference }

private final class SessionEngineSpy: VoicePCMEngine {
    var starts = 0
    var received = 0
    var cancels = 0
    var stops = 0
    var failStart = false
    var failInput = false
    func start() throws {
        starts += 1
        if failStart { throw SessionEngineFailure.unavailable }
    }
    func acceptMicrophonePCM(_ pcm16: Data) throws {
        received += 1
        if failInput { throw SessionEngineFailure.inference }
    }
    func cancelOutput() { cancels += 1 }
    func stop() { stops += 1 }
}

final class VoiceSessionControllerTests: XCTestCase {
    private func approvedGate(_ engine: SessionEngineSpy) throws -> VoiceModelGate {
        try VoiceModelGate(engine: engine, approval: VoiceModelApproval(
            approved: true, licenseReviewed: true, locallyInstalled: true, requiresExternalNetwork: false))
    }

    func testAuthAndFailedEngineStartDoNotExposeInput() throws {
        let engine = SessionEngineSpy()
        engine.failStart = true
        let session = VoiceSessionController(model: try approvedGate(engine), output: { _, _ in }, cancelPlayback: {})
        XCTAssertThrowsError(try session.start(authenticated: false))
        XCTAssertEqual(engine.starts, 0)
        XCTAssertThrowsError(try session.start(authenticated: true))
        XCTAssertEqual(session.state, .idle)
        XCTAssertThrowsError(try session.acceptMicrophoneFrame(Data(repeating: 0, count: 3_840)))
        engine.failStart = false
        try session.start(authenticated: true)
        XCTAssertEqual(session.state, .listening)
        session.stop()
    }

    func testInferenceFailureStopsSessionAndCancelsPlayback() throws {
        let engine = SessionEngineSpy()
        engine.failInput = true
        var playbackCancels = 0
        let session = VoiceSessionController(model: try approvedGate(engine),
            output: { _, _ in XCTFail("No output expected") },
            cancelPlayback: { playbackCancels += 1 })
        try session.start(authenticated: true)
        XCTAssertThrowsError(try session.acceptMicrophoneFrame(Data(repeating: 0, count: 3_840)))
        XCTAssertEqual(session.state, .idle)
        XCTAssertEqual(engine.stops, 1)
        XCTAssertEqual(engine.cancels, 1)
        XCTAssertEqual(playbackCancels, 1)
        XCTAssertThrowsError(try session.acceptMicrophoneFrame(Data(repeating: 0, count: 3_840)))
        XCTAssertEqual(engine.received, 1)
        engine.failInput = false
        try session.start(authenticated: true)
        try session.acceptMicrophoneFrame(Data(repeating: 0, count: 3_840))
        XCTAssertEqual(engine.received, 2)
        session.stop()
    }

    func testFrameAndOutputEpochAreEnforcedAcrossBargeIn() throws {
        let engine = SessionEngineSpy()
        var delivered = 0
        var cancelled = 0
        let session = VoiceSessionController(model: try approvedGate(engine), output: { _, _ in delivered += 1 },
                                             cancelPlayback: { cancelled += 1 })
        try session.start(authenticated: true)
        XCTAssertThrowsError(try session.acceptMicrophoneFrame(Data(repeating: 0, count: 3_838)))
        try session.acceptMicrophoneFrame(Data(repeating: 0, count: 3_840))
        XCTAssertEqual(engine.received, 1)
        let first = try session.beginModelOutput()
        XCTAssertThrowsError(try session.acceptMicrophoneFrame(Data(repeating: 0, count: 3_840)))
        try session.deliverModelOutput(Data(repeating: 0, count: 2_400), epoch: first)
        XCTAssertEqual(delivered, 1)
        try session.interrupt()
        XCTAssertThrowsError(try session.deliverModelOutput(Data(repeating: 0, count: 2_400), epoch: first))
        let second = try session.beginModelOutput()
        XCTAssertNotEqual(first, second)
        try session.deliverModelOutput(Data(repeating: 0, count: 2_400), epoch: second)
        try session.resumeListening()
        XCTAssertThrowsError(try session.deliverModelOutput(Data(repeating: 0, count: 2_400), epoch: second))
        try session.acceptMicrophoneFrame(Data(repeating: 0, count: 3_840))
        session.stop()
        XCTAssertThrowsError(try session.acceptMicrophoneFrame(Data(repeating: 0, count: 3_840)))
        XCTAssertEqual(engine.received, 2)
        XCTAssertEqual(delivered, 2)
        XCTAssertEqual(cancelled, 3)
        XCTAssertEqual(engine.stops, 1)
    }

    func testNormalModelOutputCompletionPreservesEngineAndRejectsStaleCallbacks() throws {
        let engine = SessionEngineSpy()
        var cancels = 0
        let session = VoiceSessionController(model: try approvedGate(engine),
            output: { _, _ in }, cancelPlayback: { cancels += 1 })
        try session.start(authenticated: true)
        let epoch = try session.beginModelOutput()
        try session.deliverModelOutput(Data(repeating: 0, count: 2_400), epoch: epoch)
        try session.finishModelOutput(epoch: epoch)
        XCTAssertEqual(session.state, .listening)
        XCTAssertEqual(cancels, 0)
        XCTAssertEqual(engine.cancels, 0)
        XCTAssertThrowsError(try session.finishModelOutput(epoch: epoch))
        XCTAssertThrowsError(try session.deliverModelOutput(Data(repeating: 0, count: 2_400), epoch: epoch))
        try session.acceptMicrophoneFrame(Data(repeating: 0, count: 3_840))
        XCTAssertEqual(engine.received, 1)
        session.stop()
    }

    func testPlaybackFailureClosesSessionAndRejectsLateAudio() throws {
        enum PlaybackFailure: Error { case unavailable }
        let engine = SessionEngineSpy()
        var playbackAttempts = 0
        var cancellations = 0
        let session = VoiceSessionController(model: try approvedGate(engine),
            output: { _, _ in
                playbackAttempts += 1
                throw PlaybackFailure.unavailable
            },
            cancelPlayback: { cancellations += 1 })
        try session.start(authenticated: true)
        let epoch = try session.beginModelOutput()
        XCTAssertThrowsError(try session.deliverModelOutput(Data(repeating: 0, count: 2_400), epoch: epoch))
        XCTAssertEqual(session.state, .idle)
        XCTAssertEqual(playbackAttempts, 1)
        XCTAssertEqual(cancellations, 1)
        XCTAssertEqual(engine.cancels, 1)
        XCTAssertEqual(engine.stops, 1)
        XCTAssertThrowsError(try session.deliverModelOutput(Data(repeating: 0, count: 2_400), epoch: epoch))
        XCTAssertThrowsError(try session.acceptMicrophoneFrame(Data(repeating: 0, count: 3_840)))
        XCTAssertEqual(playbackAttempts, 1)
        session.stop()
        XCTAssertEqual(engine.stops, 1)
    }

    func testInvalidOutputNeverReachesPlayback() throws {
        let engine = SessionEngineSpy()
        var delivered = 0
        let session = VoiceSessionController(model: try approvedGate(engine), output: { _, _ in delivered += 1 }, cancelPlayback: {})
        try session.start(authenticated: true)
        let epoch = try session.beginModelOutput()
        XCTAssertThrowsError(try session.deliverModelOutput(Data([0]), epoch: epoch))
        XCTAssertThrowsError(try session.deliverModelOutput(Data(repeating: 0, count: 4_802), epoch: epoch))
        XCTAssertEqual(delivered, 0)
        session.stop()
    }

    func testStreamingFramesRemainInSpeakingStateUntilExplicitCompletion() throws {
        let engine = SessionEngineSpy()
        var frames = 0
        var cancellations = 0
        let session = VoiceSessionController(model: try approvedGate(engine),
            output: { _, _ in frames += 1 },
            cancelPlayback: { cancellations += 1 })
        try session.start(authenticated: true)
        let epoch = try session.beginModelOutput()
        for index in 0..<3 {
            try session.deliverModelOutput(Data(repeating: UInt8(index), count: 3_840), epoch: epoch)
            XCTAssertEqual(session.state, .speaking)
            XCTAssertThrowsError(try session.acceptMicrophoneFrame(Data(repeating: 0, count: 3_840)))
        }
        XCTAssertEqual(frames, 3)
        XCTAssertEqual(cancellations, 0)
        try session.finishModelOutput(epoch: epoch)
        XCTAssertEqual(session.state, .listening)
        XCTAssertThrowsError(try session.deliverModelOutput(Data(repeating: 0, count: 3_840), epoch: epoch))
        XCTAssertThrowsError(try session.finishModelOutput(epoch: epoch))
        try session.acceptMicrophoneFrame(Data(repeating: 0, count: 3_840))
        XCTAssertEqual(engine.received, 1)
        session.stop()
    }

}
