import Foundation
import XCTest
@testable import SonnyVoiceCore

final class VoiceCaptureLifetimeTests: XCTestCase {
    func testStopInvalidatesPendingPermissionAndQueuedCallbacks() {
        let lifetime = VoiceCaptureLifetime()
        let pendingPermission = lifetime.current()
        XCTAssertTrue(lifetime.isCurrent(pendingPermission))
        lifetime.invalidate()
        XCTAssertFalse(lifetime.isCurrent(pendingPermission))
        let restarted = lifetime.current()
        XCTAssertNotEqual(pendingPermission, restarted)
        XCTAssertTrue(lifetime.isCurrent(restarted))
        lifetime.invalidate()
        XCTAssertFalse(lifetime.isCurrent(restarted))
    }

    func testConcurrentInvalidationCannotReviveOldEpoch() {
        let lifetime = VoiceCaptureLifetime()
        let old = lifetime.current()
        DispatchQueue.concurrentPerform(iterations: 64) { _ in
            lifetime.invalidate()
        }
        XCTAssertFalse(lifetime.isCurrent(old))
        XCTAssertEqual(lifetime.current(), 64)
        XCTAssertTrue(lifetime.isCurrent(64))
    }
}
