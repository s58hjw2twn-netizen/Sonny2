import Foundation
import XCTest
@testable import SonnyVoiceCore

private final class BridgeEngineSpy: VoicePCMEngine {
    func start() throws {}
    func acceptMicrophonePCM(_ pcm16: Data) throws {}
    func cancelOutput() {}
    func stop() {}
}

final class VoiceInferenceOutputBridgeTests: XCTestCase {
    private func session(_ onOutput: @escaping (Bool) -> Void) throws -> VoiceSessionController {
        let gate = try VoiceModelGate(engine: BridgeEngineSpy(), approval: VoiceModelApproval(
            approved: true, licenseReviewed: true, locallyInstalled: true, requiresExternalNetwork: false))
        let session = VoiceSessionController(model: gate,
            output: { _, _ in XCTFail("Legacy output should not run") },
            streamingOutput: { _, _, final in onOutput(final) },
            cancelPlayback: {})
        try session.start(authenticated: true)
        return session
    }

    func testBeginEmitFinishAndRejectDuplicateLifecycle() throws {
        var flags: [Bool] = []
        let controller = try session { flags.append($0) }
        let bridge = VoiceInferenceOutputBridge(session: controller)
        XCTAssertThrowsError(try bridge.emit(Data()))
        try bridge.begin()
        XCTAssertThrowsError(try bridge.begin())
        let frame = Data(repeating: 0, count: VoiceFrameAssembler.frameBytes)
        try bridge.emit(frame)
        try bridge.emit(frame, final: true)
        try bridge.finish()
        XCTAssertEqual(flags, [false, true])
        XCTAssertEqual(controller.state, .listening)
        XCTAssertThrowsError(try bridge.finish())
        controller.stop()
    }

    func testInterruptAndRevokeRejectLateInference() throws {
        var delivered = 0
        let controller = try session { _ in delivered += 1 }
        let bridge = VoiceInferenceOutputBridge(session: controller)
        try bridge.begin()
        try controller.interrupt()
        bridge.revoke()
        XCTAssertThrowsError(try bridge.emit(Data(repeating: 0, count: VoiceFrameAssembler.frameBytes)))
        XCTAssertEqual(delivered, 0)
        controller.stop()
    }

    func testInvalidFrameRevokesBridgeAndStopsSession() throws {
        let controller = try session { _ in XCTFail("Invalid frame reached speaker") }
        let bridge = VoiceInferenceOutputBridge(session: controller)
        try bridge.begin()
        XCTAssertThrowsError(try bridge.emit(Data([0])))
        XCTAssertThrowsError(try bridge.emit(Data(repeating: 0, count: VoiceFrameAssembler.frameBytes)))
        XCTAssertEqual(controller.state, .speaking)
        // Invalid frames are rejected before speaker delivery; caller owns teardown.
        controller.stop()
    }
    func testStaleFinishReleasesBridgeEpochAfterInterruption() throws {
        let controller = try session { _ in }
        let bridge = VoiceInferenceOutputBridge(session: controller)
        try bridge.begin()
        try controller.interrupt()
        XCTAssertThrowsError(try bridge.finish()) { error in
            XCTAssertEqual(error as? VoiceSessionError, .staleOutput)
        }
        try controller.resumeListening()
        // A revoked output must not permanently block a subsequent turn.
        try bridge.begin()
        try bridge.emit(Data(repeating: 0, count: VoiceFrameAssembler.frameBytes), final: true)
        try bridge.finish()
        controller.stop()
    }

    func testPrematureFinishRemainsRecoverableUntilFinalFrame() throws {
        let controller = try session { _ in }
        let bridge = VoiceInferenceOutputBridge(session: controller)
        try bridge.begin()
        XCTAssertThrowsError(try bridge.finish())
        try bridge.emit(Data(repeating: 0, count: VoiceFrameAssembler.frameBytes), final: true)
        try bridge.finish()
        XCTAssertEqual(controller.state, .listening)
        controller.stop()
    }

    func testStoppedSessionRejectsLateFinishAsStale() throws {
        let controller = try session { _ in }
        let bridge = VoiceInferenceOutputBridge(session: controller)
        try bridge.begin()
        controller.stop()
        XCTAssertThrowsError(try bridge.finish()) { error in
            XCTAssertEqual(error as? VoiceSessionError, .staleOutput)
        }
        XCTAssertThrowsError(try bridge.emit(Data(repeating: 0, count: VoiceFrameAssembler.frameBytes)))
    }

    func testInterruptedTurnCannotFinishAfterNewTurnBegins() throws {
        let controller = try session { _ in }
        let staleBridge = VoiceInferenceOutputBridge(session: controller)
        try staleBridge.begin()
        try controller.interrupt()
        try controller.resumeListening()
        let freshBridge = VoiceInferenceOutputBridge(session: controller)
        try freshBridge.begin()
        XCTAssertThrowsError(try staleBridge.finish()) { error in
            XCTAssertEqual(error as? VoiceSessionError, .staleOutput)
        }
        try freshBridge.emit(Data(repeating: 0, count: VoiceFrameAssembler.frameBytes), final: true)
        try freshBridge.finish()
        controller.stop()
    }

}
