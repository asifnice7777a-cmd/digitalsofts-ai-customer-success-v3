from app.memory.session_memory import SessionMemory


def test_session_memory_update_and_get():
    memory = SessionMemory()
    memory.update_profile("s1", client_name="John Doe", company="Acme Inc")
    profile = memory.get("s1").profile
    assert profile.client_name == "John Doe"
    assert profile.company == "Acme Inc"


def test_session_memory_reset():
    memory = SessionMemory()
    memory.update_profile("s2", client_name="Jane")
    memory.reset("s2")
    profile = memory.get("s2").profile
    assert profile.client_name is None


def test_session_memory_history():
    memory = SessionMemory()
    memory.add_message("s3", "user", "Hello")
    session = memory.get("s3")
    assert len(session.history) == 1
    assert session.history[0]["content"] == "Hello"
