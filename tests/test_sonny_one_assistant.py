from sonny_one.assistant import SonnyOneAssistant
from sonny_one.runtime import SonnyOneRuntime

class FakeModel:
    def __init__(self):
        self.calls = []
    def generate(self, *, system, user):
        self.calls.append((system,user))
        return "Acknowledged."

def test_assistant_uses_user_scoped_context(tmp_path):
    runtime = SonnyOneRuntime(str(tmp_path/"memory.db"))
    runtime.remember_confirmed("alice","Likes structured reports","user",consent=True)
    model = FakeModel()
    assistant = SonnyOneAssistant(runtime,model)
    response = assistant.reply("bob","Hello")
    assert response.text == "Acknowledged."
    assert response.memory_count == 0
    assert "Likes structured reports" not in model.calls[-1][1]
    response = assistant.reply("alice","Hello")
    assert response.memory_count == 1
    assert "Likes structured reports" in model.calls[-1][1]

def test_assistant_rejects_empty_request(tmp_path):
    import pytest
    assistant = SonnyOneAssistant(SonnyOneRuntime(str(tmp_path/"memory.db")),FakeModel())
    with pytest.raises(ValueError):
        assistant.reply("alice"," ")
