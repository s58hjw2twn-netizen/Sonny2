#if os(iOS)
import Foundation
import SwiftUI
import SonnyVoiceCore

/// Local-only device verification UI. A deterministic diagnostic engine receives
/// microphone frames; it is NOT a speech model or authenticated assistant.
@MainActor
final class VoiceDemoModel: ObservableObject {
    @Published var status = "Not started"
    @Published var framesCaptured = 0
    @Published var diagnosticFrames = 0
    private let io = SonnyAudioIO()
    private let turns = VoiceTurnGate()
    private let diagnostic = VoiceDiagnosticPCMEngine()
    private var session: VoiceSessionController?
    private var lastCapturedFrame: Data?
    private var startPending = false
    private var startGeneration: UInt64 = 0

    func start() {
        guard !startPending && turns.state == .idle else { return }
        startPending = true
        startGeneration &+= 1
        let generation = startGeneration
        lastCapturedFrame = nil
        framesCaptured = 0
        diagnosticFrames = 0
        Task {
            defer { startPending = false }
            do {
                // These flags describe only the locally built diagnostic engine.
                // They do not authenticate a user or authorize an external model.
                let model = try VoiceModelGate(engine: diagnostic, approval: VoiceModelApproval(
                    approved: true, licenseReviewed: true, locallyInstalled: true,
                    requiresExternalNetwork: false))
                let controller = VoiceSessionController(model: model, turns: turns,
                    output: { [weak self] pcm, epoch in
                        guard let self else { throw VoiceSessionError.staleOutput }
                        try self.io.enqueueOutput(pcm, epoch: epoch, gate: self.turns)
                    },
                    cancelPlayback: { [weak self] in self?.io.interruptOutput() })
                try controller.start(authenticated: true) // In-process diagnostic only.
                session = controller
                try await io.start(authenticated: true) { [weak self] frame in
                    Task { @MainActor [weak self] in
                        guard let self, self.startGeneration == generation else { return }
                        self.lastCapturedFrame = frame
                        self.framesCaptured += 1
                        guard let session = self.session, session.state == .listening else { return }
                        do {
                            try session.acceptMicrophoneFrame(frame)
                            self.diagnosticFrames = self.diagnostic.framesReceived
                        } catch {
                            self.stop()
                            self.status = "Diagnostic input failed: \(error.localizedDescription)"
                        }
                    }
                }
                guard startGeneration == generation else {
                    stop()
                    return
                }
                status = "Microphone → local diagnostic active (no AI or network)"
            } catch {
                io.stop()
                session?.stop()
                session = nil
                if startGeneration == generation {
                    status = "Start failed: \(error.localizedDescription)"
                }
            }
        }
    }

    /// Manually exercise the controller-to-speaker path using captured PCM.
    /// Never automatically echo microphone audio while capturing.
    func playCapturedSample() {
        guard let frame = lastCapturedFrame else {
            status = "Capture microphone audio before playback"
            return
        }
        do {
            guard let session else { status = "Start microphone first"; return }
            let epoch = try session.beginModelOutput()
            try session.deliverModelOutput(frame, epoch: epoch)
            status = "Queued local 80 ms playback (no AI)"
        } catch { status = "Sample playback failed: \(error.localizedDescription)" }
    }

    func playTone() {
        do {
            guard let session else { status = "Start microphone first"; return }
            let epoch = try session.beginModelOutput()
            let tone = (0..<2_400).map { i in
                Float(sin(2 * Double.pi * 440 * Double(i) / 24_000) * 0.1)
            }
            try session.deliverModelOutput(VoiceWire.pcm16(from: tone), epoch: epoch)
            status = "Queued 100 ms diagnostic speaker tone"
        } catch { status = "Playback failed: \(error.localizedDescription)" }
    }

    func interrupt() {
        do {
            guard let session else { status = "Start microphone first"; return }
            try session.interrupt()
            try session.resumeListening()
            status = "Playback cancelled; diagnostic listening resumed"
        } catch { status = "Interrupt unavailable: \(error.localizedDescription)" }
    }

    func stop() {
        startGeneration &+= 1
        lastCapturedFrame = nil
        session?.stop()
        session = nil
        io.stop()
        status = "Stopped"
    }
}

@main
struct SonnyVoiceDemoApp: App {
    @StateObject private var model = VoiceDemoModel()
    @Environment(\.scenePhase) private var scenePhase

    var body: some Scene {
        WindowGroup {
            VStack(spacing: 20) {
                Text("Sonny ONE Voice — device I/O test").font(.title2)
                Text(model.status).multilineTextAlignment(.center)
                Text("PCM frames captured: \(model.framesCaptured)")
                Text("Frames accepted by diagnostic: \(model.diagnosticFrames)")
                Button("Start microphone") { model.start() }
                Button("Play test tone") { model.playTone() }
                Button("Play last captured sample") { model.playCapturedSample() }
                Button("Interrupt output") { model.interrupt() }
                Button("Stop") { model.stop() }
                Text("Local-only diagnostic; no speech recognition, model, server, or audio upload.")
                    .font(.footnote)
            }
            .padding()
            .onDisappear { model.stop() }
            .onChange(of: scenePhase) { _, phase in
                if phase != .active { model.stop() }
            }
        }
    }
}
#endif
