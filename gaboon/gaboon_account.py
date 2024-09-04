from pathlib import Path
from eth_account import Account
from eth_account.signers.local import (
    LocalAccount,
)
from eth_keys.datatypes import (
    PrivateKey,
)
from hexbytes import HexBytes
from gaboon.constants.vars import DEFAULT_KEYSTORES_PATH
from eth_utils import to_bytes
from gaboon.commands.wallet import decrypt_key
from typing import cast


class GaboonAccount:
    def __init__(
        self,
        private_key: str | bytes | None = None,
        keystore_path_or_account_name: Path | str | None = None,
        password: str = None,
        password_file_path: Path = None,
    ):
        self._private_key = private_key
        self._local_account: LocalAccount | None = None
        if private_key:
            private_key = to_bytes(hexstr=private_key)
        private_key = cast(bytes, private_key)
        if keystore_path_or_account_name:
            self.keystore_path: Path = (
                keystore_path_or_account_name
                if isinstance(keystore_path_or_account_name, Path)
                else DEFAULT_KEYSTORES_PATH.joinpath(keystore_path_or_account_name)
            )
            private_key = self.unlock(
                password=password, password_file_path=password_file_path
            )
        if not private_key:
            raise Warning("Be sure to call unlock before trying to send a transaction.")
        self._local_account = LocalAccount(PrivateKey(private_key), Account())

    def __getattr__(self, name):
        if self._local_account is not None:
            try:
                return getattr(self._local_account, name)
            except AttributeError:
                pass
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    def set_keystore_path(self, keystore_path: Path | str):
        if isinstance(keystore_path, str):
            keystore_path = DEFAULT_KEYSTORES_PATH.joinpath(Path(keystore_path))
        self.keystore_path = keystore_path

    def set_private_key(self, private_key: str | HexBytes):
        self._private_key = (
            private_key if isinstance(private_key, HexBytes) else HexBytes(private_key)
        )

    def unlocked(self) -> bool:
        return self._private_key is not None

    def unlock(
        self,
        password: str = None,
        password_file_path: Path = None,
        prompt_even_if_unlocked: bool = False,
    ) -> HexBytes:
        if password_file_path:
            password_file_path = Path(password_file_path).expanduser().resolve()
        if not self.unlocked() or prompt_even_if_unlocked:
            if self.keystore_path is None:
                raise Exception(
                    "No keystore path provided. Set it with set_keystore_path (path)"
                )
            self._private_key = decrypt_key(
                self.keystore_path.stem,
                password=password,
                password_file_path=password_file_path,
                keystores_path=self.keystore_path.parent,
            )
        return cast(HexBytes, self._private_key)
