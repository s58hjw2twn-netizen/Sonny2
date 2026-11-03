#if os(iOS)
import AVFoundation
import Foundation
import SonnyVoiceCore

/// Native audio I/O harness. Add this file to an iOS app target and link SonnyVoiceCore.
/// No model, socket, or privileged assistant tool is instantiated by this class.
@MainActor
public final class SonnyAudioIO {
    public enum AudioError: Error {
        case unauthenticated
        case microphoneDenied
        case invalidInputFormat
        case outputQueueFull
        case notRunning
        case staleOutput
        case startCancelled
    }

    private let engine = AVAudioEngine()
    private let player = AVAudioPlayerNode()
    private let processingQueue = DispatchQueue(label: "sonny.voice.capture", qos: .userInitiated)
    private let captureSlots = DispatchSemaphore(value: 4)
    private let outputFormat = AVAudioFormat(standardFormatWithSampleRate: 24_000, channels: 1)!
    private var notificationTokens: [NSObjectProtocol] = []
    private var tapInstalled = false
    private var running = false
    private var pendingBuffers = 0
    private var playbackGeneration: UInt64 = 0
    private let maxPendingBuffers = 8
    private let lifetime = VoiceCaptureLifetime()

    public init() {
        engine.attach(player)
        engine.connect(player, to: engine.mainMixerNode, format: outputFormat)
    }

    /// Caller must establish its own authenticated assistant session before starting.
    /// Callback is in-process PCM16 only; never send it over unauthenticated transport.
    public func start(authenticated: Bool,
                      onPCMFrame: @escaping @Sendable (Data) -> Void,
                      onAudioRouteInvalidated: @escaping @MainActor () -> Void) async throws {
        guard authenticated else { throw AudioError.unauthenticated }
        guard !running else { return }
        let requestedEpoch = lifetime.current()
        guard await AVAudioApplication.requestRecordPermission() else {
            throw AudioError.microphoneDenied
        }
        // Stop/background during the asynchronous permission dialog must not
        // start a microphone later when the user returns to the application.
        guard lifetime.isCurrent(requestedEpoch) else { throw AudioError.startCancelled }
        let session = AVAudioSession.sharedInstance()
        try session.setCategory(.playAndRecord, mode: .voiceChat,
                                options: [.defaultToSpeaker, .allowBluetooth])
        try session.setActive(true)

        let input = engine.inputNode
        let hardwareFormat = input.inputFormat(forBus: 0)
        guard hardwareFormat.commonFormat == .pcmFormatFloat32,
              !hardwareFormat.isInterleaved,
              let monoInput = AVAudioFormat(standardFormatWithSampleRate: hardwareFormat.sampleRate,
                                            channels: 1),
              let converter = AVAudioConverter(from: monoInput, to: outputFormat) else {
            try? session.setActive(false)
            throw AudioError.invalidInputFormat
        }
        let queue = processingQueue
        let slots = captureSlots
        let targetFormat = outputFormat
        let lifetime = self.lifetime
        let captureEpoch = requestedEpoch
        // A new assembler is created for each capture session; old queued work
        // is rejected by captureEpoch after stop/restart.
        let continuity = VoiceCaptureContinuity()
        let captureFramer = VoiceCaptureFramer(continuity: continuity)
        input.installTap(onBus: 0, bufferSize: 1024, format: hardwareFormat) { buffer, _ in
            guard slots.wait(timeout: .now()) == .success else {
                continuity.markDropped()
                return
            }
            guard let channels = buffer.floatChannelData, buffer.frameLength > 0 else {
                continuity.markDropped()
                slots.signal()
                return
            }
            // Copy before returning from the real-time audio callback.
            let captured = Array(UnsafeBufferPointer(start: channels[0], count: Int(buffer.frameLength)))
            let audioGeneration = continuity.snapshot()
            queue.async {
                defer { slots.signal() }
                guard lifetime.isCurrent(captureEpoch),
                      continuity.isCurrent(audioGeneration) else { return }
                guard let source = AVAudioPCMBuffer(pcmFormat: monoInput,
                                                    frameCapacity: AVAudioFrameCount(captured.count)) else { return }
                source.frameLength = AVAudioFrameCount(captured.count)
                captured.withUnsafeBufferPointer { values in
                    source.floatChannelData?[0].update(from: values.baseAddress!, count: values.count)
                }
                let capacity = AVAudioFrameCount(ceil(Double(captured.count) * 24_000 / monoInput.sampleRate)) + 256
                guard let output = AVAudioPCMBuffer(pcmFormat: targetFormat, frameCapacity: capacity) else { return }
                var supplied = false
                var conversionError: NSError?
                converter.convert(to: output, error: &conversionError) { _, status in
                    if supplied {
                        status.pointee = .noDataNow
                        return nil
                    }
                    supplied = true
                    status.pointee = .haveData
                    return source
                }
                guard conversionError == nil,
                      let samples = output.floatChannelData,
                      output.frameLength > 0 else {
                    continuity.markDropped()
                    return
                }
                let count = Int(output.frameLength)
                var offset = 0
                while offset < count {
                    let end = min(offset + VoiceWire.maxFrameBytes / 2, count)
                    let chunk = Array(UnsafeBufferPointer(start: samples[0] + offset, count: end - offset))
                    guard lifetime.isCurrent(captureEpoch),
                          continuity.isCurrent(audioGeneration) else { return }
                    guard let pcm = try? VoiceWire.pcm16(from: chunk),
                          let frames = try? captureFramer.append(pcm, generation: audioGeneration) else {
                        continuity.markDropped()
                        return
                    }
                    for frame in frames where lifetime.isCurrent(captureEpoch)
                        && continuity.isCurrent(audioGeneration) {
                        onPCMFrame(frame)
                    }
                    offset = end
                }
            }
        }
        tapInstalled = true
        do {
            try engine.start()
            player.play()
            running = true
        } catch {
            stop()
            throw error
        }
        for name in [AVAudioSession.interruptionNotification, AVAudioSession.routeChangeNotification] {
            notificationTokens.append(NotificationCenter.default.addObserver(
                forName: name, object: session, queue: nil
            ) { [weak self] _ in
                // The notification may be delivered after stop/restart. Only the
                // capture session that registered this observer may invalidate I/O.
                Task { @MainActor [weak self] in
                    guard let self, self.lifetime.isCurrent(captureEpoch) else { return }
                    self.stop()
                    onAudioRouteInvalidated()
                }
            })
        }
    }

    /// A model's output must carry the current VoiceTurnGate epoch.
    public func enqueueOutput(_ pcm16: Data, epoch: UInt64, gate: VoiceTurnGate) throws {
        guard running else { throw AudioError.notRunning }
        guard gate.acceptsOutput(epoch: epoch) else { throw AudioError.staleOutput }
        guard pendingBuffers < maxPendingBuffers else { throw AudioError.outputQueueFull }
        let samples = try VoiceWire.floats(from: pcm16)
        guard let buffer = AVAudioPCMBuffer(pcmFormat: outputFormat,
                                           frameCapacity: AVAudioFrameCount(samples.count)) else {
            throw AudioError.invalidInputFormat
        }
        buffer.frameLength = AVAudioFrameCount(samples.count)
        samples.withUnsafeBufferPointer { values in
            buffer.floatChannelData?[0].update(from: values.baseAddress!, count: values.count)
        }
        pendingBuffers += 1
        let generation = playbackGeneration
        player.scheduleBuffer(buffer, completionCallbackType: .dataPlayedBack) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self = self, self.playbackGeneration == generation else { return }
                self.pendingBuffers = max(0, self.pendingBuffers - 1)
            }
        }
    }

    /// Call immediately when barge-in is detected, before acknowledging interruption.
    public func interruptOutput() {
        playbackGeneration &+= 1
        pendingBuffers = 0
        player.stop() // Drops scheduled buffers, not just currently audible audio.
        if running { player.play() }
    }

    public func stop() {
        lifetime.invalidate()
        interruptOutput()
        if tapInstalled {
            engine.inputNode.removeTap(onBus: 0)
            tapInstalled = false
        }
        engine.stop()
        running = false
        for token in notificationTokens { NotificationCenter.default.removeObserver(token) }
        notificationTokens.removeAll()
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
    }
}
#endif
