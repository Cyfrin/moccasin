"""
Wallet management utilities

Usage: gab wallet <COMMAND>

Commands:
  list              List all the accounts in the keystore default directory [aliases: ls]
  generate          Add a new account with a random private key [aliases: g]
  import            Import a private key into an encrypted keystore [aliases: i]
  help              Print this message or the help of the given subcommand(s)

Options:
  -h, --help  Print help
"""

import json
import getpass
from pathlib import Path
import shutil
from typing import Any, List
from gaboon.logging import logger
from gaboon.constants import DEFAULT_KEYSTORES_PATH
from eth_account import Account as EthAccountsClass
from eth_account.signers.local import LocalAccount


def main(args: List[Any]) -> int:
    if args.wallet_command == "list":
        list_accounts()
        return 0
    elif args.wallet_command == "generate":
        return generate_account(
            args.name,
            args.save,
            password=args.password,
            password_file=args.password_file,
        )
    elif args.wallet_command == "import":
        return import_private_key(args.name)
    elif args.wallet_command == "delete":
        return delete_keystore(args.keystore_file_name)
    else:
        logger.error(f"Unknown accounts command: {args.wallet_command}")
        return 1


def list_accounts(
    keystores_path: Path = DEFAULT_KEYSTORES_PATH,
) -> list[Any] | None:
    if keystores_path.exists():
        account_paths = sorted(keystores_path.glob("*"))
        logger.info(
            f"Found {len(account_paths)} account{'s' if len(account_paths)!=1 else ''}:"
        )
        for path in account_paths:
            logger.info(f"{path.stem}")
        return account_paths
    else:
        logger.info(f"No accounts found at {keystores_path}")
        return None


def generate_account(
    name: str, save: bool = False, password: str = None, password_file: str = None
) -> int:
    logger.info("Generating new account...")
    new_account: LocalAccount = EthAccountsClass.create()
    if save:
        if password:
            save_to_keystores(
                name,
                new_account,
                password=password,
                keystores_path=DEFAULT_KEYSTORES_PATH,
            )
        elif password_file:
            save_to_keystores(
                name,
                new_account,
                password_file=Path(password_file),
                keystores_path=DEFAULT_KEYSTORES_PATH,
            )
        else:
            logger.error("No password provided to save account")
            return 1
    else:
        logger.info(f"Account generated: {new_account.address}")
        logger.info(f"(Unsafe) Private key: {new_account.key}")
        logger.info(
            f"To save, add the --save flag next time with:\ngab wallet generate {name} --save --password <password>"
        )
    return 0


def save_to_keystores(
    name: str,
    account: LocalAccount,
    password: str = None,
    password_file: Path | None = None,
    keystores_path: Path = DEFAULT_KEYSTORES_PATH,
):
    new_keystore_path = keystores_path.joinpath(name)
    if new_keystore_path.exists():
        logger.error(f"Account with name {name} already exists")
        return 1
    new_keystore_path.mkdir(exist_ok=True)
    json_file = new_keystore_path.joinpath(name).resolve()
    if password:
        encrypted: dict[str, Any] = account.encrypt(password)
    elif password_file:
        with password_file.open("r") as fp:
            password = fp.read()
        encrypted: dict[str, Any] = account.encrypt(password)
    else:
        logger.error("No password provided to save account")
        return 1
    with json_file.open("w") as fp:
        json.dump(encrypted, fp)
    logger.info(f"Saved account {name} to keystores!")


def import_private_key(name: str) -> int:
    logger.info(f"Importing private key...")
    while True:
        private_key = getpass.getpass("Enter your private key: ")
        if private_key:
            break
        logger.error("Private key cannot be empty. Please try again.")

    # Step 2 & 3: Get password and confirmation
    while True:
        password = getpass.getpass("Enter a password to encrypt your key: ")
        if not password:
            logger.error("Password cannot be empty. Please try again.")
            continue

        password_confirm = getpass.getpass("Confirm your password: ")
        if password == password_confirm:
            break
        logger.error("Passwords do not match. Please try again.")

    new_account: LocalAccount = EthAccountsClass.from_key(private_key)
    save_to_keystores(
        name,
        new_account,
        password=password,
    )


def delete_keystore(
    keystore_file_name: str,
    keystores_path: Path = DEFAULT_KEYSTORES_PATH,
) -> int:
    keystore_path = keystores_path.joinpath(keystore_file_name)

    if not keystore_path.exists():
        logger.error(
            f"Account with name {keystore_file_name} does not exist in keystores"
        )
        return 1

    try:
        if keystore_path.is_dir():
            shutil.rmtree(keystore_path)
        else:
            keystore_path.unlink()
        logger.info(f"Successfully deleted account {keystore_file_name} from keystores")
        return 0
    except Exception as e:
        logger.error(
            f"Failed to delete account {keystore_file_name} from keystores: {str(e)}"
        )
        return 1
