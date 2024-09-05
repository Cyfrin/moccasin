from argparse import Namespace
from pathlib import Path
from gaboon.logging import logger
import code
import readline
from gaboon.config import get_config, initialize_global_config
from gaboon._sys_path_and_config_setup import (
    _patch_sys_path,
    _setup_network_and_account_from_args,
)
from gaboon.constants.vars import DEFAULT_GABOON_FOLDER, CONSOLE_HISTORY_FILE
import atexit

def main(args: Namespace) -> int:
    initialize_global_config()
    config = get_config()
    config_root = config.get_root()
    
    # Set up the environment (add necessary paths to sys.path, etc.)
    with _patch_sys_path([config_root, config_root / config.contracts_folder]):
        _setup_network_and_account_from_args(
            network=args.network,
            url=args.url,
            fork=args.fork,
        )
        
        # Ensure the Gaboon folder exists
        DEFAULT_GABOON_FOLDER.mkdir(parents=True, exist_ok=True)
        
        history_file = DEFAULT_GABOON_FOLDER.joinpath(CONSOLE_HISTORY_FILE)
        validate_history_file(history_file)
        history_file_str = str(history_file)
        
        
        # Enable history
        readline.parse_and_bind("tab: complete")
        
        # Try to read the history file
        try:
            readline.read_history_file(history_file_str)
        except FileNotFoundError:
            print("No history file found. Starting with empty history.")
        except Exception as e:
            print(f"Error reading history file: {e}")
            print("Starting with empty history.")
        
        # Set history length
        readline.set_history_length(1000)
        
        # Save history on exit
        atexit.register(readline.write_history_file, history_file_str)
        
        local_vars = globals().copy()
        local_vars.update(locals())
        console = GaboonConsole(local_vars)
        
        # Run the console
        console.interact("Welcome to the interactive console! Your command history will be saved.")    
    return 0

def validate_history_file(history_file: Path) -> None:
    HISTORY_HEADER = "_HiStOrY_V2_\n"
    MIN_VALID_SIZE = 10

    if not history_file.exists():
        logger.debug("History file does not exist. A new one will be created.")
        return

    file_size = history_file.stat().st_size
    logger.debug(f"History file exists. Size: {file_size} bytes")

    if file_size < MIN_VALID_SIZE:
        logger.debug("History file is too small. Appending header.")
        with history_file.open('a') as f:
            f.write(HISTORY_HEADER)


class GaboonConsole(code.InteractiveConsole):
    def __init__(self, locals=None, filename="<console>"):
        super().__init__(locals, filename)
        self.exit_requested = False

    def raw_input(self, prompt=""):
        line = input(prompt)
        if line.strip().lower() == 'q':
            self.exit_requested = True
            raise EOFError("Quit requested")
        return line

    def interact(self, banner=None, exitmsg=None):
        try:
            super().interact(banner, exitmsg)
        except EOFError:
            if self.exit_requested:
                print("Exiting console...")
            else:
                raise