import Foundation

/// State and generation gate for stale audio. No speech command authorizes tools.
public enum VoiceTurnState: Equatable {
    case idle, listening, speaking, interrupted
}

public enum VoiceTurnError: Error, Equatable {
    case unauthenticated
    case invalidTransition
}

public final class VoiceTurnGate {
    public private(set) var state: VoiceTurnState = .idle
    public private(set) var outputEpoch: UInt64 = 0

    public init() {}

    public func start(authenticated: Bool) throws {
        guard authenticated else { throw VoiceTurnError.unauthenticated }
        guard state == .idle && outputEpoch != UInt64.max else { throw VoiceTurnError.invalidTransition }
        state = .listening
    }

    @discardableResult
    public func beginOutput() throws -> UInt64 {
        guard (state == .listening || state == .interrupted) && outputEpoch < UInt64.max - 1 else {
            throw VoiceTurnError.invalidTransition
        }
        advanceEpoch()
        state = .speaking
        return outputEpoch
    }

    public func acceptsOutput(epoch: UInt64) -> Bool {
        state == .speaking && outputEpoch != UInt64.max && epoch == outputEpoch
    }

    /// Mark a model turn complete only after its final output has finished.
    /// A late completion from an interrupted/restarted turn must not resume input.
    public func finishOutput(epoch: UInt64) throws {
        guard state == .speaking && epoch == outputEpoch else {
            throw VoiceTurnError.invalidTransition
        }
        advanceEpoch()
        state = .listening
    }

    public func interrupt() throws {
        guard state == .speaking else { throw VoiceTurnError.invalidTransition }
        advanceEpoch()
        state = .interrupted
    }

    public func resumeListening() throws {
        guard state == .interrupted || state == .speaking else {
            throw VoiceTurnError.invalidTransition
        }
        advanceEpoch()
        state = .listening
    }

    // Exhaustion is terminal: never reuse an epoch that may authorize stale audio.
    private func advanceEpoch() {
        if outputEpoch < UInt64.max { outputEpoch += 1 }
    }

    public func stop() {
        advanceEpoch()
        state = .idle
    }
}
