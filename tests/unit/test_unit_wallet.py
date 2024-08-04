from pathlib import Path
from typing import List
from gaboon.commands.wallet import inspect, list_accounts
from tests.conftest import (
    ANVIL1_KEYSTORE_NAME,
    ANVIL_KEYSTORE_SAVED,
)


def test_inspect(anvil_keystore):
    result = inspect(ANVIL1_KEYSTORE_NAME, keystores_path=anvil_keystore)
    assert result["address"] == ANVIL_KEYSTORE_SAVED["address"]


def test_list_accounts(anvil_keystore):
    accounts: List[Path] = list_accounts(keystores_path=anvil_keystore)
    assert len(accounts) == 1
    assert accounts[0].stem == ANVIL1_KEYSTORE_NAME
