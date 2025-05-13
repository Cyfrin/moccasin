from moccasin._error_utils import handle_vvm_error
from pathlib import Path
from unittest import mock
from vvm.exceptions import VyperError as VVMVyperError


def test_handle_vvm_error_with_different_temp_dirs():
    """Tests the handle_vvm_error function with various temporary directory paths."""
    contract_path = Path("src/AssignError.vy")

    # Simulate different temporary directory paths
    temp_dirs = [
        "/tmp",
        "/var/folders/some/random/T",
        "/var/folders/h6/j1dkww4j5k9bvjpqtkyqcp3r0000gn/T",
        "C:\\Users\\User\\AppData\\Local\\Temp",
        "/private/tmp",
        "C:\\TEMP",
        "C:\\tmp",
        "/usr/tmp",
    ]

    for temp_dir in temp_dirs:
        with mock.patch("tempfile.gettempdir", return_value=temp_dir):
            # Simulate the error message as it would appear in the VVMVyperError
            simulated_stderr = (
                f'contract "{temp_dir}/vyper-abcdef123456.vy:12": some error message'
            )
            simulated_command = [temp_dir, "vyper", str(contract_path)]
            simulated_stdout = f"Error compiling: {temp_dir}/vyper-abcdef123456.vy"

            original_error = VVMVyperError(
                message="vvm.exceptions.VyperError: An error occurred during execution",
                stderr_data=simulated_stderr,
                stdout_data=simulated_stdout,
                return_code=1,
                command=simulated_command,
            )

            # Call the function to handle the error
            try:
                handle_vvm_error(original_error, contract_path)
            except VVMVyperError as excinfo:
                print(temp_dir)
                # Check that the error message was modified correctly
                assert str(contract_path) in excinfo.stderr_data
                assert (
                    f'contract "{str(contract_path)}:12": some error message'
                    in excinfo.stderr_data
                )
                # Check that the command was modified correctly in stderr_data and not in stdout_data
                assert (
                    f"Error compiling: {temp_dir}/vyper-abcdef123456.vy"
                    in excinfo.stdout_data
                )
                assert temp_dir not in excinfo.stderr_data
