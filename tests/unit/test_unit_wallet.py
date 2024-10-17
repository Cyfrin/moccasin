from pathlib import Path
from typing import List

from moccasin.commands.wallet import list_accounts, view_wallet
from tests.conftest import ANVIL1_KEYSTORE_NAME

ANVIL1_KEYSTORE = {
    "address": "f39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    "crypto": {
        "cipher": "aes-128-ctr",
        "cipherparams": {"iv": "ae9712fe1bc4134b395927044adc64a5"},
        "ciphertext": "87d3e99bdf044eb04d25b1d12056b4f3f08c055e1ec45b76aeffc54fbfe53978",
        "kdf": "scrypt",
        "kdfparams": {
            "dklen": 32,
            "n": 262144,
            "r": 8,
            "p": 1,
            "salt": "d5edcd1d453e22684c7a90556b724266",
        },
        "mac": "0acb7e94a5d855f9d39a4169707afdf496af7e255ae02d08fcfccd313b6d1535",
    },
    "id": "902de108-8694-49eb-b752-4d84d257e9ab",
    "version": 3,
}


def test_view_wallet(anvil_keystore):
    result = view_wallet(ANVIL1_KEYSTORE_NAME, keystores_path=anvil_keystore)
    assert result["address"] == ANVIL1_KEYSTORE["address"]


def test_list_accounts(anvil_keystore):
    accounts: List[Path] = list_accounts(keystores_path=anvil_keystore)
    assert len(accounts) == 1
    assert accounts[0].stem == ANVIL1_KEYSTORE_NAME
