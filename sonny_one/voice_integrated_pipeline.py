"""Authenticated, provider-independent turn coordination. No network or audio inference."""
from sonny_one.voice_adapter import VoiceSession, VoiceState
from sonny_one.voice_turn_coordinator import VoiceTurnCoordinator, TurnState

class IntegratedVoicePipeline:
    def __init__(self, provider, *, authenticated=False):
        if authenticated is not True:
            raise PermissionError('authenticated channel required')
        self.session = VoiceSession(provider, authenticated=True)
        self.turns = VoiceTurnCoordinator(authenticated=True, cancel_output=self._cancel)
        self._closed = False

    def _cancel(self):
        if self.session.state is not VoiceState.SPEAKING:
            raise RuntimeError('speech state mismatch')
        self.session.resume_listening()

    def start(self):
        self._require_open()
        self.session.start()
        self.turns.start()

    def submit(self, transcript):
        self._require_open()
        if self.session.state is not VoiceState.LISTENING:
            raise RuntimeError('audio session not listening')
        return self.turns.submit_transcript(transcript)

    def deliver(self, ticket, response):
        self._require_open()
        if self.session.state is not VoiceState.LISTENING:
            return False
        if self.turns.state is TurnState.THINKING and ticket == self.turns._active:
            if not isinstance(response, str) or not response.strip() or len(response) > 8192:
                raise ValueError('invalid response')
            self.session.begin_output()
            try:
                return self.turns.accept_response(ticket, response)
            except BaseException:
                self.session.resume_listening()
                raise
        return False

    def interrupt(self):
        self._require_open()
        self.turns.interrupt()

    def output_finished(self, ticket):
        self._require_open()
        if self.turns.state is not TurnState.SPEAKING or ticket != self.turns._active:
            return False
        self.session.resume_listening()
        return self.turns.output_finished(ticket)

    def close(self):
        if self._closed:
            return
        self.turns.close()
        self.session.close()
        self._closed = True

    def _require_open(self):
        if self._closed:
            raise RuntimeError('pipeline closed')
