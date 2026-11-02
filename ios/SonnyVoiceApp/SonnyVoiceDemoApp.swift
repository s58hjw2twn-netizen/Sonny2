#if os(iOS)
import Foundation
import SwiftUI
import SonnyVoiceCore

/// Local-only device verification UI; deliberately contains no inference or network code.
@MainActor
final class VoiceDemoModel: ObservableObject {
    @Published var status = "Not started"
    @Published var framesCaptured = 0
    private let io = SonnyAudioIO()
    private let turns = VoiceTurnGate()
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
        Task {
            defer { startPending = false }
            do {
                // This is an in-process audio test, NOT authenticated assistant access.
                try turns.start(authenticated: true)
                try await io.start(authenticated: true) { [weak self] frame in
                    Task { @MainActor [weak self] in
                        guard let self = self, self.startGeneration == generation else { return }
                        self.lastCapturedFrame = frame
                        self.framesCaptured += 1
                    }
                }
                guard startGeneration == generation else {
                    io.stop()
                    turns.stop()
                    return
                }
                status = "Capturing locally (no network or AI model)"
            } catch {
                io.stop()
                turns.stop()
                status = "Start failed: \(error.localizedDescription)"
            }
        }
    }

    /// A manual, local-only 80 ms microphone-to-speaker diagnostic.
    /// Never automatically echo captured audio while the microphone is live.
    func playCapturedSample() {
        guard let frame = lastCapturedFrame else {
            status = "Capture microphone audio before playback"
            return
        }
        do {
            let epoch = try turns.beginOutput()
            try io.enqueueOutput(frame, epoch: epoch, gate: turns)
            status = "Queued captured 80 ms sample (local-only)"
        } catch { status = "Sample playback failed: \(error.localizedDescription)" }
    }

    func playTone() {
        do {
            let epoch = try turns.beginOutput()
            let tone = (0..<2400).map { i in
                Float(sin(2 * Double.pi * 440 * Double(i) / 24_000) * 0.1)
            }
            try io.enqueueOutput(VoiceWire.pcm16(from: tone), epoch: epoch, gate: turns)
            status = "Played 100 ms speaker test tone"
        } catch { status = "Playback failed: \(error.localizedDescription)" }
    }

    func interrupt() {
        io.interruptOutput()
        do {
            try turns.interrupt()
            try turns.resumeListening()
            status = "Output cancelled; microphone remains active"
        } catch { status = "Interrupt unavailable: \(error.localizedDescription)" }
    }

    func stop() {
        startGeneration &+= 1
        lastCapturedFrame = nil
        io.stop()
        turns.stop()
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
                Button("Start microphone") { model.start() }
                Button("Play test tone") { model.playTone() }
                Button("Play last captured sample") { model.playCapturedSample() }
                Button("Interrupt output") { model.interrupt() }
                Button("Stop") { model.stop() }
                Text("Local-only test. No model, server, or recording upload. Interrupt to reset playback.")
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
