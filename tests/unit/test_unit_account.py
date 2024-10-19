from moccasin.moccasin_account import MoccasinAccount


def test_can_load_account_with_prompt(monkeypatch, anvil_keystore):
    responses = iter(["wrong", "password"])
    monkeypatch.setattr("getpass.getpass", lambda _: next(responses))

    m_account = MoccasinAccount.load(anvil_keystore.joinpath("anvil1"))
    assert isinstance(m_account, MoccasinAccount)
    assert m_account.is_unlocked() is True


def test_can_load_account_no_prompt(anvil_keystore):
    m_account = MoccasinAccount.load(
        anvil_keystore.joinpath("anvil1"), password="password"
    )
    assert isinstance(m_account, MoccasinAccount)
    assert m_account.is_unlocked() is True
