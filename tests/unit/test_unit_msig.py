from prompt_toolkit import PromptSession


def test_prompt_example(pt_session):
    pt_session.send_text("hello\n")
    session = PromptSession(input=pt_session)
    assert session.prompt("Say hi: ") == "hello"
