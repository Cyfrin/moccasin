from pathlib import Path
from typing import cast

from boa.util.abi import Address
from eth_account import Account
from eth_account.signers.local import LocalAccount
from eth_keys.datatypes import PrivateKey
from eth_typing import ChecksumAddress
from eth_utils import to_bytes
from eth_utils.address import to_checksum_address
from hexbytes import HexBytes

from moccasin.commands.wallet import decrypt_key
from moccasin.constants.vars import MOCCASIN_KEYSTORE_PATH
from moccasin.logging import logger


class MoccasinAccount(LocalAccount):
    def __init__(
        self,
        private_key: str | bytes | None = None,
        keystore_path_or_account_name: Path | str | None = None,
        password: str = None,
        password_file_path: Path = None,
        address: Address | None = None,
        ignore_warning: bool = False,
    ):
        # We override the LocalAccount Type
        self._private_key: bytes | None = None  # type: ignore
        # We override the LocalAccount Type
        self._address: ChecksumAddress | None = None  # type: ignore
        self._publicapi = Account()

        if address:
            self._address = to_checksum_address(address)

        if private_key:
            private_key = to_bytes(hexstr=private_key)
        private_key = cast(bytes, private_key)
        if keystore_path_or_account_name:
            self.keystore_path: Path = (
                keystore_path_or_account_name
                if isinstance(keystore_path_or_account_name, Path)
                else MOCCASIN_KEYSTORE_PATH.joinpath(keystore_path_or_account_name)
            )
            private_key = self.unlock(
                password=password, password_file_path=password_file_path
            )

        if private_key:
            self._init_key(private_key)
        else:
            if not ignore_warning:
                logger.warning(
                    "Be sure to call unlock before trying to send a transaction."
                )

    @property
    def private_key(self) -> bytes:
        return self.key

    @property
    def address(self) -> ChecksumAddress | None:  # type: ignore
        if self.private_key:
            return PrivateKey(self.private_key).public_key.to_checksum_address()
        if self._address:
            return self._address
        return None

    def _init_key(self, private_key: bytes | HexBytes):
        if isinstance(private_key, HexBytes):
            private_key = bytes(private_key)
        private_key_converted = PrivateKey(private_key)
        self._address = private_key_converted.public_key.to_checksum_address()
        key_raw: bytes = private_key_converted.to_bytes()
        self._private_key = key_raw
        self._key_obj: PrivateKey = private_key_converted

    def set_keystore_path(self, keystore_path: Path | str):
        if isinstance(keystore_path, str):
            keystore_path = MOCCASIN_KEYSTORE_PATH.joinpath(Path(keystore_path))
        self.keystore_path = keystore_path

    def unlocked(self) -> bool:
        return self.private_key is not None

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
            decrypted_key = decrypt_key(
                self.keystore_path.stem,
                password=password,
                password_file_path=password_file_path,
                keystores_path=self.keystore_path.parent,
            )
            self._init_key(decrypted_key)
        return cast(HexBytes, self.private_key)

    @classmethod
    def from_boa_address(cls, address: Address) -> "MoccasinAccount":
        return cls()
