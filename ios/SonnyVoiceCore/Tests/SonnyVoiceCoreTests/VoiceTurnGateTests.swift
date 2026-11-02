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
}
