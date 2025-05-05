import re
from pathlib import Path

from vvm.exceptions import VyperError as VVMVyperError


def handle_vvm_error(error: VVMVyperError, contract_path: Path) -> None:
    """Handle VVM errors by adapting the error message and raising the exception.
    @param error: The VVMVyperError instance to handle.
    @param contract_path: The path to the contract file.
    @raises VVMVyperError: Raises a modified VVMVyperError with the updated error message.
    """
    original_stderr = error.stderr_data
    temporary_path_pattern = r'contract "/tmp/vyper-[a-zA-Z0-9_-]+\.vy:(\d+)"'
    replacement_string = f'contract "{str(contract_path)}:\\1"'

    # Replace the temporary path with the actual contract path
    modified_stderr = re.sub(
        temporary_path_pattern, replacement_string, original_stderr
    )
    raise VVMVyperError(
        stderr_data=modified_stderr,
        stdout_data=error.stdout_data,
        return_code=error.return_code,
        command=error.command,
    )
