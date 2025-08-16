import json
import traceback
from argparse import Namespace
from typing import Tuple

from eth_typing import URI
from prompt_toolkit import HTML, PromptSession, print_formatted_text
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from safe_eth.eth import EthereumClient
from safe_eth.safe import Safe, SafeTx

from moccasin._sys_path_and_config_setup import (
    _patch_sys_path,
    _setup_network_and_account_from_config_and_cli,
    get_sys_paths_list,
)
from moccasin.config import get_config, initialize_global_config
from moccasin.logging import logger, set_log_level
from moccasin.moccasin_account import MoccasinAccount
from moccasin.msig_cli.common_prompts import (
    prompt_continue_next_step,
    prompt_rpc_url,
    prompt_safe_address,
    prompt_save_safe_tx_json,
)
from moccasin.msig_cli.tx import tx_build, tx_sign
from moccasin.msig_cli.tx.sign_prompts import (
    prompt_eip712_input_file,
    prompt_is_right_account,
)
from moccasin.msig_cli.utils.helpers import (
    build_safe_tx_from_message,
    extract_safe_tx_json,
    get_custom_eip712_structured_data,
    get_safe_instance,
    get_signatures_bytes,
    save_safe_tx_json,
    validate_ethereum_client_chain_id,
)
from moccasin.msig_cli.utils.types import T_SafeTxData

# --- Constants ---
TX_BUILD_CMD = "tx-build"
TX_SIGN_CMD = "tx-sign"
TX_BROADCAST_CMD = "tx-broadcast"

# Define the command order for transaction commands
TX_COMMANDS_ORDER = [TX_BUILD_CMD, TX_SIGN_CMD, TX_BROADCAST_CMD]


# --- Prompt session functions ---
def _bottom_toolbar_cli(
    ethereum_client: EthereumClient = None,
    safe_instance: Safe = None,
    safe_tx: SafeTx = None,
):
    """Return the bottom toolbar text for the prompt session."""
    chain_id = "None"
    safe_addr = "None"
    tx_signed_counter = "None"

    if ethereum_client:
        chain_id = ethereum_client.get_chain_id()
    if safe_instance:
        safe_addr = safe_instance.address
    if safe_tx and safe_instance:
        try:
            threshold = safe_instance.retrieve_threshold()
        except Exception:
            threshold = "?"
        try:
            signers_count = len(getattr(safe_tx, "signers", []))
        except Exception:
            signers_count = "?"
        tx_signed_counter = f"{signers_count}/{threshold}"

    return HTML(
        f"<cyan>ChainId: {chain_id} | Safe: {safe_addr} | Signed: {tx_signed_counter}</cyan>"
    )


def _right_toolbar_cli(msig_command: str = None):
    """Return the right toolbar text for the prompt session, showing the current tx command."""
    if msig_command:
        return HTML(f"<b><orange bg='ansiblack'>&lt;{msig_command}&gt;</orange></b>")
    return HTML("<b><orange bg='ansiblack'>&lt;msig&gt;</orange></b>")


def _update_bottom_toolbar(
    prompt_session: PromptSession,
    ethereum_client: EthereumClient,
    safe_instance: Safe = None,
    safe_tx: SafeTx = None,
):
    """Update the bottom toolbar of the prompt session with the current state."""
    prompt_session.bottom_toolbar = _bottom_toolbar_cli(
        ethereum_client=ethereum_client, safe_instance=safe_instance, safe_tx=safe_tx
    )


def _prompt_save_json(
    prompt_session: PromptSession, safe_tx: SafeTx, output_json: str = None
):
    """Prompt the user to save the SafeTx JSON data."""
    safe_tx_data = get_custom_eip712_structured_data(safe_tx)
    if output_json is None:
        output_json = prompt_save_safe_tx_json(prompt_session)

    if output_json is not None:
        save_safe_tx_json(output_json, safe_tx_data)
    else:
        print_formatted_text(HTML("<b><yellow>Not saving EIP-712 JSON.</yellow></b>"))


# --- Tx command functions ---
def _tx_build_command(
    prompt_session: PromptSession,
    ethereum_client: EthereumClient,
    args: Namespace = None,
) -> Tuple[Safe, SafeTx]:
    """Handle the transaction building command.

    This method initializes the Safe instance and SafeTx based on the provided or prompted input,
    validates the chainId, and then runs the transaction builder.

    :param args: Optional argparse Namespace with command arguments.
    """
    print_formatted_text(
        HTML("\n\n<b><cyan>Running tx_builder command...</cyan></b>\n")
    )
    # Validate and preprocess the provided arguments if not None
    (safe_address, to, value, operation, safe_nonce, data, gas_token, output_json) = (
        tx_build.preprocess_raw_args(args)
    )

    # Values to build from tx_build
    safe_instance = None
    safe_tx = None

    # Initialize Safe instance from args if provided
    if safe_address is None:
        print_formatted_text(
            HTML("<b><yellow>Warning: Missing safe address from input.</yellow></b>")
        )
        safe_address = prompt_safe_address(prompt_session)

    # Init Safe instance
    safe_instance = get_safe_instance(
        ethereum_client=ethereum_client, safe_address=safe_address
    )
    if safe_instance is None:
        logger.error(f"Failed to initialize Safe instance with address: {safe_address}")
        raise ValueError(
            f"Failed to initialize Safe instance with address: {safe_address}"
        )

    print_formatted_text(
        HTML(f"<b><green>Using Safe address: {safe_instance.address}</green></b>")
    )

    # Update bottom toolbar with Ethereum client
    _update_bottom_toolbar(
        prompt_session=prompt_session,
        ethereum_client=ethereum_client,
        safe_instance=safe_instance,
    )

    # Run the transaction builder with the provided args
    try:
        safe_tx = tx_build.run(
            prompt_session=prompt_session,
            safe_instance=safe_instance,
            to=to,
            value=value,
            operation=operation,
            safe_nonce=safe_nonce,
            data=data,
            gas_token=gas_token,
            output_json=output_json,
        )
    except Exception as e:
        raise Exception("Failed to build SafeTx from provided parameters: {e}") from e

    # Update bottom toolbar with Ethereum client
    _update_bottom_toolbar(
        prompt_session=prompt_session,
        ethereum_client=ethereum_client,
        safe_instance=safe_instance,
        safe_tx=safe_tx,
    )

    # Prompt to save the SafeTx JSON data
    _prompt_save_json(
        prompt_session=prompt_session, safe_tx=safe_tx, output_json=output_json
    )

    return safe_instance, safe_tx


def _tx_sign_command(
    prompt_session: PromptSession,
    ethereum_client: EthereumClient,
    safe_instance: Safe = None,
    safe_tx: SafeTx = None,
    args: Namespace = None,
) -> Tuple[Safe, SafeTx, MoccasinAccount]:
    """Handle the transaction signing command.

    This method initializes the Safe instance and SafeTx based on the provided or prompted input file,
    validates the chainId, and then runs the signing process.

    It will go directly to signing if the SafeTx is already available,
    or prompt for the EIP-712 JSON input file if not.

    :param args: Optional argparse Namespace with command arguments.
    """
    print_formatted_text(HTML("\n\n<b><cyan>Running tx_sign command...</cyan></b>"))
    # Validate and preprocess the provided arguments if not None
    (input_file_safe_tx, output_file_safe_tx) = tx_sign.preprocess_raw_args(args)

    # No prior data means we need to get the Safe from the input file
    if not safe_instance and not safe_tx:
        # Check if eip712_input_file is provided, else prompt to get it
        if input_file_safe_tx is None:
            print_formatted_text(
                HTML(
                    "<b><yellow>Warning: No input file provided. Prompting for custom or original EIP-712 JSON file.</yellow></b>"
                )
            )
            print_formatted_text(
                HTML(
                    "<b><magenta>Note: Advised to run tx_build before tx_sign if no input file available.</magenta></b>\n"
                )
            )
            eip712_prompted_file = prompt_eip712_input_file(prompt_session)
            if not eip712_prompted_file.exists():
                raise ValueError(f"JSON file SafeTx not found: {eip712_prompted_file}.")
            input_file_safe_tx = eip712_prompted_file

        # Load the JSON file
        with open(input_file_safe_tx, "r") as f:
            safe_tx_json: T_SafeTxData = json.loads(f.read())

        # Extract SafeTx data from input file
        domain_json, message_json, signatures_json = extract_safe_tx_json(safe_tx_json)
        if domain_json is None or message_json is None:
            raise ValueError(
                "Invalid SafeTx JSON format: missing 'domain' or 'message' fields."
            )

        # Validate the domain chainId from JSON and our Ethereum client
        validate_ethereum_client_chain_id(
            ethereum_client=ethereum_client, domain_json=domain_json
        )

        # Initialize Safe instance with the address from domain_json
        safe_address = domain_json.get("verifyingContract")
        if not safe_address:
            raise ValueError(
                "Domain JSON must contain 'verifyingContract' field for Safe address."
            )
        safe_instance = get_safe_instance(
            ethereum_client=ethereum_client, safe_address=safe_address
        )
        print_formatted_text(
            HTML(f"<b><green>Using Safe address: {safe_instance.address}</green></b>")
        )

        # Initialize SafeTx with the message and signatures
        safe_tx = build_safe_tx_from_message(
            safe_instance=safe_instance,
            message_json=message_json,
            signatures_json=get_signatures_bytes(signatures_json),
        )

        # Update bottom toolbar with Ethereum client
        _update_bottom_toolbar(
            prompt_session=prompt_session,
            ethereum_client=ethereum_client,
            safe_instance=safe_instance,
        )

    # Get the signer from config or prompt if not provided
    signer = None
    if args.account is not None or args.private_key is not None:
        signer = get_config().get_active_network().get_default_account()
        if signer is None:
            raise ValueError(
                "No signer account found in config for the provided arguments."
            )
    else:
        # Prompt for signer account if not provided in args
        signer = tx_sign.get_signer_account(prompt_session)
        if signer is None:
            raise ValueError("No signer account provided or found.")

    # Validate the signer account
    if signer is not None and signer.address is not None:
        # Check if the account is the right one
        is_right_account = prompt_is_right_account(prompt_session, signer.address)
        if is_right_account.lower() not in ("yes", "y"):
            raise ValueError("User aborted tx_sign command due to wrong account.")

    # Display the initialized account
    print_formatted_text(
        HTML(
            f"\n<b><green>Signer account initialized successfully: {signer.address}</green></b>\n"
        )
    )

    # Sign the SafeTx with the provided signer
    try:
        safe_tx = tx_sign.run(
            prompt_session=prompt_session,
            safe_instance=safe_instance,
            safe_tx=safe_tx,
            signer=signer,
            output_file_safe_tx=output_file_safe_tx,
        )
    except Exception as e:
        raise Exception(f"Failed to sign SafeTx with provided parameters: {e}") from e

    # Update bottom toolbar with Ethereum client
    _update_bottom_toolbar(
        prompt_session=prompt_session,
        ethereum_client=ethereum_client,
        safe_instance=safe_instance,
        safe_tx=safe_tx,
    )

    # Prompt to save the SafeTx JSON data
    _prompt_save_json(
        prompt_session=prompt_session, safe_tx=safe_tx, output_json=output_file_safe_tx
    )

    return safe_instance, safe_tx, signer


def _tx_broadcast_command(self, args: Namespace = None):
    """Run the transaction broadcast command.

    :param args: Optional argparse Namespace with command arguments.
    """
    print_formatted_text(
        HTML("<b><red>tx_broadcast command not implemented yet!</red></b>")
    )


# --- Main Function ---
def main(args: Namespace) -> int:
    """Main entry point for the msig CLI."""
    try:
        # Set prompt session for user interactions
        prompt_session = PromptSession(
            auto_suggest=AutoSuggestFromHistory(), validate_while_typing=False
        )
        # Set the right toolbar with default msig
        prompt_session.rprompt = _right_toolbar_cli()

        # If a network is specified, use it; otherwise, prompt for RPC URL
        rpc_url = args.url
        if args.network is None and rpc_url is None:
            rpc_url = prompt_rpc_url(prompt_session)

        # Initialize global configuration without requiring a TOML file
        config = initialize_global_config(is_default_project=args.no_project_toml)
        set_log_level(quiet=args.quiet, debug=args.debug)
        with _patch_sys_path(get_sys_paths_list(config)):
            _setup_network_and_account_from_config_and_cli(
                network=args.network,
                url=str(rpc_url),
                fork=args.fork,
                account=args.account,
                private_key=args.private_key,
                password=args.password,
                password_file_path=args.password_file_path,
                prompt_live=args.prompt_live,
            )
            # @TODO prompt for Metamask UI setup later
            config = get_config()

            # Initialize Ethereum client
            ethereum_client = EthereumClient(URI(config.get_active_network().url))

            if ethereum_client is not None:
                # Print the chain ID in a formatted way
                print_formatted_text(
                    HTML(
                        f"<b><green>Using ChainId: {ethereum_client.get_chain_id()}</green></b>"
                    )
                )
            else:
                logger.error("Failed to initialize Ethereum client.")
                return 1

            # Update bottom toolbar with Ethereum client
            _update_bottom_toolbar(
                prompt_session=prompt_session, ethereum_client=ethereum_client
            )

            # Handle the msig command
            msig_command = str(args.msig_command)
            if msig_command.startswith("tx"):
                # Init Safe instance and SafeTx
                safe_instance = None
                safe_tx = None
                signer = None

                # Prepare the tx command workflow
                if msig_command not in TX_COMMANDS_ORDER:
                    logger.error(
                        f"Unknown msig command: {msig_command}. Expected one of {TX_COMMANDS_ORDER}."
                    )
                    return 1

                # Run the main loop for the tx commands
                start_idx = TX_COMMANDS_ORDER.index(msig_command)
                for idx in range(start_idx, len(TX_COMMANDS_ORDER)):
                    cmd = TX_COMMANDS_ORDER[idx]
                    # Set the right toolbar with the current command
                    prompt_session.rprompt = _right_toolbar_cli(cmd)

                    if cmd == TX_BUILD_CMD:
                        safe_instance, safe_tx = _tx_build_command(
                            prompt_session, ethereum_client, args
                        )
                    elif cmd == TX_SIGN_CMD:
                        safe_instance, safe_tx, signer = _tx_sign_command(
                            prompt_session,
                            ethereum_client,
                            safe_instance,
                            safe_tx,
                            args,
                        )
                    elif cmd == TX_BROADCAST_CMD:
                        _tx_broadcast_command(prompt_session, args)

                    # Reset command in right toolbar after each command
                    msig_command = None

                    # Set signer to boa env eoa to use in next commands
                    if signer is not None:
                        config.get_active_network().set_boa_eoa(signer)

                    # Only prompt for next step if:
                    # 1. Not the last command in the order
                    if idx < len(TX_COMMANDS_ORDER) - 1:
                        # 2. Sign onlt if we have a safe_tx after building
                        if not safe_tx and cmd == "tx_sign":
                            print_formatted_text(
                                HTML(
                                    "<b><red>SafeTx not created. Aborting following signing.</red></b>"
                                )
                            )
                            break

                        # 3. safe_tx has been signed with required signers
                        if (
                            cmd == "tx_sign"
                            and len(safe_tx.signers)
                            < safe_instance.retrieve_threshold()
                        ):
                            print_formatted_text(
                                HTML(
                                    "<b><red>SafeTx not signed by enough signers. Aborting following broadcasting.</red></b>"
                                )
                            )
                            break

                        # Reset the right toolbar
                        prompt_session.rprompt = _right_toolbar_cli()

                        # Prompt for next step
                        next_step = prompt_continue_next_step(
                            prompt_session, next_cmd=TX_COMMANDS_ORDER[idx + 1]
                        )
                        if not next_step:
                            break
            else:
                logger.error(
                    f"Unknown msig command: {msig_command}. Expected one of tx_build, tx_sign, or tx_broadcast."
                )
                return 1

    except Exception as e:
        logger.error(f"Error in msig CLI: {e}")
        traceback.print_exc()
        return 1
    except KeyboardInterrupt:
        logger.info("User aborted the msig CLI.")
        return 1

    # Print success message and return 0
    print_formatted_text(HTML("<b><green>msig CLI completed successfully.</green></b>"))
    # Return 0 for successful completion
    print_formatted_text(HTML("<b><cyan>Shutting down msig CLI...</cyan></b>"))
    return 0
