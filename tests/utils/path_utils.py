import traceback
from subprocess import CalledProcessError
from pathlib import Path


def restore_original_path_in_error(
    error: Exception, temp_path: Path, original_path: Path
) -> None:
    """Replace occurrences of a temporary path in an exception's traceback with the original path.

    This function takes an exception, a temporary path, and an original path as input.
    It will replace all occurrences of the temporary path in the exception's traceback with the original path.
    It will then print the modified traceback and re-raise the original exception.
    Also handles `subprocess.CalledProcessError` by modifying its stdout and stderr.

    :param error: The original exception raised.
    :type error: Exception
    :param temp_path: The temporary path to be replaced.
    :type temp_path: str
    :param original_path: The original path to replace it with.
    :type original_path: str
    :return Exception: The original exception with an adjusted traceback (printed separately).
    """
    if isinstance(error, CalledProcessError):
        # Modify stdout and stderr in CalledProcessError
        if error.stdout:
            error.stdout = error.stdout.replace(str(temp_path), str(original_path))
        if error.stderr:
            error.stderr = error.stderr.replace(str(temp_path), str(original_path))
        # Print the modified error output
        if error.stdout:
            print(error.stdout)
        if error.stderr:
            print(error.stderr)
    else:
        # Format and modify the traceback
        tb_list = traceback.format_exception(type(error), error, error.__traceback__)
        tb_modified = [
            line.replace(str(temp_path), str(original_path)) for line in tb_list
        ]

        # Print the modified traceback
        print("".join(tb_modified))

    # Exit the program to suppress the default traceback output
    return error.with_traceback(error.__traceback__)
