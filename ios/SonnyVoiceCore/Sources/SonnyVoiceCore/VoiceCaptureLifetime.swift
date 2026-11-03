import Foundation

/// Thread-safe lifetime token for native audio callbacks and permission requests.
/// A stopped session must never accept work queued by an earlier capture epoch.
public final class VoiceCaptureLifetime: @unchecked Sendable {
    private let lock = NSLock()
    private var epoch: UInt64 = 0

    public init() {}

    public func current() -> UInt64 {
        lock.lock()
        defer { lock.unlock() }
        return epoch
    }

    public func invalidate() {
        lock.lock()
        defer { lock.unlock() }
        // Exhaustion is terminal; never wrap to a previously valid token.
        if epoch < UInt64.max { epoch += 1 }
    }

    public func isCurrent(_ value: UInt64) -> Bool {
        lock.lock()
        defer { lock.unlock() }
        return epoch != UInt64.max && epoch == value
    }
}
