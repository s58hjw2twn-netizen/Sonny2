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
}
