import Foundation

/// Serialized handoff from an asynchronous inference worker to VoiceSessionController.
/// Call all methods on the same executor as the session controller; never from an
/// audio render callback. The bridge does not load models or grant model approval.
public final class VoiceInferenceOutputBridge {
    private let session: VoiceSessionController
    private var epoch: UInt64?

    public init(session: VoiceSessionController) { self.session = session }

    /// Starts a new output turn. A second start cannot silently replace an active turn.
    @discardableResult
    public func begin() throws -> UInt64 {
        guard epoch == nil else { throw VoiceTurnError.invalidTransition }
        let newEpoch = try session.beginModelOutput()
        epoch = newEpoch
        return newEpoch
    }

    /// Deliver exactly one bounded PCM16 frame; caller is responsible for
    /// resampling model output to the VoiceWire contract before invoking this.
    public func emit(_ pcm16: Data, final: Bool = false) throws {
        guard let current = epoch else { throw VoiceSessionError.staleOutput }
        do {
            try session.deliverModelOutput(pcm16, epoch: current, isFinalFrame: final)
        } catch {
            epoch = nil
            throw error
        }
    }

    /// Call only after the speaker has drained the last emitted frame.
    public func finish() throws {
        guard let current = epoch else { throw VoiceSessionError.staleOutput }
        do {
            try session.finishModelOutput(epoch: current)
            epoch = nil
        } catch VoiceSessionError.staleOutput {
            // The session has revoked this turn; do not retain a dead epoch.
            epoch = nil
            throw VoiceSessionError.staleOutput
        }
    }

    /// Explicitly revoke pending worker output after stop or interruption.
    /// The owning session must also be interrupted/stopped to revoke its epoch.
    public func revoke() { epoch = nil }
}
