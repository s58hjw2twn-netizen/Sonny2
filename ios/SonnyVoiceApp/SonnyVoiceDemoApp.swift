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

    func start() {
        Task {
            do {
                // This is an in-process audio test, NOT authenticated assistant access.
                try turns.start(authenticated: true)
                try await io.start(authenticated: true) { [weak self] _ in
                    Task { @MainActor [weak self] in self?.framesCaptured += 1 }
                }
                status = "Capturing locally (no network or AI model)"
            } catch {
                io.stop()
                turns.stop()
                status = "Start failed: \(error.localizedDescription)"
            }
        }
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
        io.stop()
        turns.stop()
        status = "Stopped"
    }
}

@main
struct SonnyVoiceDemoApp: App {
    @StateObject private var model = VoiceDemoModel()

    var body: some Scene {
        WindowGroup {
            VStack(spacing: 20) {
                Text("Sonny ONE Voice — device I/O test").font(.title2)
                Text(model.status).multilineTextAlignment(.center)
                Text("PCM frames captured: \(model.framesCaptured)")
                Button("Start microphone") { model.start() }
                Button("Play test tone") { model.playTone() }
                Button("Interrupt output") { model.interrupt() }
                Button("Stop") { model.stop() }
                Text("Local-only test. No model, server, or recording upload.")
                    .font(.footnote)
            }
            .padding()
            .onDisappear { model.stop() }
        }
    }
}
#endif
