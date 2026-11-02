import pytest
from sonny_one.voice_turn_coordinator import VoiceTurnCoordinator, TurnState, TurnTicket

def make():
    calls=[]
    return VoiceTurnCoordinator(authenticated=True,cancel_output=lambda:calls.append('cancel')),calls

def test_auth():
    with pytest.raises(PermissionError): VoiceTurnCoordinator(cancel_output=lambda:None)

def test_basic():
    v,c=make();v.start();t=v.submit_transcript('hello');assert v.accept_response(t,'hi');assert v.output_finished(t);assert v.state is TurnState.LISTENING;assert not c

def test_interrupt_thinking_rejects_late_response():
    v,c=make();v.start();t=v.submit_transcript('hello');v.interrupt();assert not v.accept_response(t,'stale');assert not c

def test_interrupt_speaking_cancels_and_rejects_old_completion():
    v,c=make();v.start();t=v.submit_transcript('hello');v.accept_response(t,'hi');v.interrupt();assert c==['cancel'];assert not v.output_finished(t)

def test_cancel_failure_preserves_speaking_state():
    def fail(): raise RuntimeError('device')
    v=VoiceTurnCoordinator(authenticated=True,cancel_output=fail);v.start();t=v.submit_transcript('x');v.accept_response(t,'y');
    with pytest.raises(RuntimeError):v.interrupt()
    assert v.state is TurnState.SPEAKING

def test_replay_and_forged_ticket_rejected():
    v,c=make();v.start();t=v.submit_transcript('x');assert not v.accept_response(TurnTicket('forged',t.turn),'y');assert v.accept_response(t,'y');assert not v.accept_response(t,'again')

def test_close_invalidates_inflight():
    v,c=make();v.start();t=v.submit_transcript('x');v.close();assert not v.accept_response(t,'y');assert v.state is TurnState.CLOSED

def test_close_speaking_cancels():
    v,c=make();v.start();t=v.submit_transcript('x');v.accept_response(t,'y');v.close();assert c==['cancel']

def test_input_limits():
    v,c=make();v.start()
    for x in ('', '  ', 'x'*4097, None):
        with pytest.raises(ValueError):v.submit_transcript(x)

def test_response_limits():
    v,c=make();v.start();t=v.submit_transcript('x')
    for x in ('', ' '*4, 'x'*8193, None):
        with pytest.raises(ValueError):v.accept_response(t,x)

def test_wrong_state():
    v,c=make()
    with pytest.raises(RuntimeError):v.submit_transcript('x')
    with pytest.raises(RuntimeError):v.interrupt()
    v.start()
    with pytest.raises(RuntimeError):v.start()
