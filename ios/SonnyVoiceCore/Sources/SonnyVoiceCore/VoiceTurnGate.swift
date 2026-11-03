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
        guard state == .idle else { throw VoiceTurnError.invalidTransition }
        state = .listening
    }

    @discardableResult
    public func beginOutput() throws -> UInt64 {
        guard state == .listening || state == .interrupted else {
            throw VoiceTurnError.invalidTransition
        }
        outputEpoch &+= 1
        state = .speaking
        return outputEpoch
    }

    public func acceptsOutput(epoch: UInt64) -> Bool {
        state == .speaking && epoch == outputEpoch
    }

    /// Mark a model turn complete only after its final output has finished.
    /// A late completion from an interrupted/restarted turn must not resume input.
    public func finishOutput(epoch: UInt64) throws {
        guard state == .speaking && epoch == outputEpoch else {
            throw VoiceTurnError.invalidTransition
        }
        outputEpoch &+= 1
        state = .listening
    }

    public func interrupt() throws {
        guard state == .speaking else { throw VoiceTurnError.invalidTransition }
        outputEpoch &+= 1
        state = .interrupted
    }

    public func resumeListening() throws {
        guard state == .interrupted || state == .speaking else {
            throw VoiceTurnError.invalidTransition
        }
        outputEpoch &+= 1
        state = .listening
    }

    public func stop() {
        outputEpoch &+= 1
        state = .idle
    }
}
