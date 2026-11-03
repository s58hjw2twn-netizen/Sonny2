import Foundation

public enum VoiceSessionError: Error, Equatable {
    case notListening
    case staleOutput
}

/// Coordinates a locally approved PCM engine with the microphone/output turn gate.
/// This is a control-plane boundary, not a model implementation or authenticated transport.
/// All methods and callbacks must run on one serialized executor (the iOS main actor).
public final class VoiceSessionController {
    private let model: VoiceModelGate
    private let turns: VoiceTurnGate
    private let output: (Data, UInt64) throws -> Void
    private let cancelPlayback: () -> Void

    public var state: VoiceTurnState { turns.state }

    public init(model: VoiceModelGate,
                turns: VoiceTurnGate = VoiceTurnGate(),
                output: @escaping (Data, UInt64) throws -> Void,
                cancelPlayback: @escaping () -> Void) {
        self.model = model
        self.turns = turns
        self.output = output
        self.cancelPlayback = cancelPlayback
    }

    public func start(authenticated: Bool) throws {
        try turns.start(authenticated: authenticated)
        do {
            try model.start()
        } catch {
            turns.stop()
            throw error
        }
    }

    /// Never forward microphone audio while a prior model turn is speaking.
    /// Frames must be exactly 80 ms of 24 kHz mono signed PCM16.
    public func acceptMicrophoneFrame(_ pcm16: Data) throws {
        guard turns.state == .listening else { throw VoiceSessionError.notListening }
        // Malformed frames are rejected without tearing down an otherwise
        // healthy session. An engine failure, however, must end the session.
        guard pcm16.count == VoiceFrameAssembler.frameBytes else {
            throw VoiceModelError.invalidMoshiFrame
        }
        do {
            try model.acceptMoshiFrame(pcm16)
        } catch {
            stop()
            throw error
        }
    }

    public func beginModelOutput() throws -> UInt64 {
        try turns.beginOutput()
    }

    /// Reject late asynchronous model output after interruption, restart or stop.
    public func deliverModelOutput(_ pcm16: Data, epoch: UInt64) throws {
        guard turns.acceptsOutput(epoch: epoch) else { throw VoiceSessionError.staleOutput }
        try VoiceWire.validateFrame(pcm16)
        do {
            try output(pcm16, epoch)
        } catch {
            // A failed audio device/queue must not leave the model speaking
            // indefinitely or allow late output from the failed turn.
            stop()
            throw error
        }
    }

    /// Normal end-of-turn is distinct from interruption: playback has already
    /// drained, so do not cancel the engine or speaker on successful completion.
    public func finishModelOutput(epoch: UInt64) throws {
        try turns.finishOutput(epoch: epoch)
    }

    /// Invalidate the old epoch before cancelling playback and model output.
    public func interrupt() throws {
        try turns.interrupt()
        cancelPlayback()
        model.cancelOutput()
    }

    public func resumeListening() throws {
        try turns.resumeListening()
        cancelPlayback()
        model.cancelOutput()
    }

    public func stop() {
        turns.stop()
        cancelPlayback()
        model.stop()
    }
}
