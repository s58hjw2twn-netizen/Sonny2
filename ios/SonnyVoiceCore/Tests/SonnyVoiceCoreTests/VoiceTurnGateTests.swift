import XCTest
@testable import SonnyVoiceCore

final class VoiceTurnGateTests: XCTestCase {
    func testAuthenticationAndBargeInDiscardStaleOutput() throws {
        let gate = VoiceTurnGate()
        XCTAssertThrowsError(try gate.start(authenticated: false))
        XCTAssertEqual(gate.state, .idle)
        try gate.start(authenticated: true)
        let oldEpoch = try gate.beginOutput()
        XCTAssertTrue(gate.acceptsOutput(epoch: oldEpoch))
        try gate.interrupt()
        XCTAssertFalse(gate.acceptsOutput(epoch: oldEpoch))
        let newEpoch = try gate.beginOutput()
        XCTAssertNotEqual(oldEpoch, newEpoch)
        XCTAssertFalse(gate.acceptsOutput(epoch: oldEpoch))
        XCTAssertTrue(gate.acceptsOutput(epoch: newEpoch))
        try gate.resumeListening()
        XCTAssertFalse(gate.acceptsOutput(epoch: newEpoch))
        gate.stop()
        XCTAssertEqual(gate.state, .idle)
    }

    func testNormalOutputCompletionResumesListeningWithoutAcceptingLateAudio() throws {
        let gate = VoiceTurnGate()
        try gate.start(authenticated: true)
        let first = try gate.beginOutput()
        try gate.finishOutput(epoch: first)
        XCTAssertEqual(gate.state, .listening)
        XCTAssertFalse(gate.acceptsOutput(epoch: first))
        XCTAssertThrowsError(try gate.finishOutput(epoch: first))
        let second = try gate.beginOutput()
        XCTAssertThrowsError(try gate.finishOutput(epoch: first))
        XCTAssertTrue(gate.acceptsOutput(epoch: second))
        try gate.interrupt()
        XCTAssertThrowsError(try gate.finishOutput(epoch: second))
    }

    func testInvalidTransitionsFailClosed() throws {
        let gate = VoiceTurnGate()
        XCTAssertThrowsError(try gate.beginOutput())
        XCTAssertThrowsError(try gate.interrupt())
        try gate.start(authenticated: true)
        XCTAssertThrowsError(try gate.start(authenticated: true))
        XCTAssertThrowsError(try gate.resumeListening())
        gate.stop()
        XCTAssertThrowsError(try gate.beginOutput())
    }
    func testRestartRejectsPriorSessionAudioAndCompletion() throws {
        let gate = VoiceTurnGate()
        try gate.start(authenticated: true)
        let oldEpoch = try gate.beginOutput()
        gate.stop()
        XCTAssertFalse(gate.acceptsOutput(epoch: oldEpoch))
        XCTAssertThrowsError(try gate.start(authenticated: false))
        XCTAssertEqual(gate.state, .idle)
        try gate.start(authenticated: true)
        XCTAssertThrowsError(try gate.finishOutput(epoch: oldEpoch))
        let currentEpoch = try gate.beginOutput()
        XCTAssertNotEqual(oldEpoch, currentEpoch)
        XCTAssertFalse(gate.acceptsOutput(epoch: oldEpoch))
        XCTAssertThrowsError(try gate.finishOutput(epoch: oldEpoch))
        XCTAssertTrue(gate.acceptsOutput(epoch: currentEpoch))
        try gate.finishOutput(epoch: currentEpoch)
        XCTAssertEqual(gate.state, .listening)
    }
}
