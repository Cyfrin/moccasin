import traceback
from pathlib import Path

from moccasin.logging import logger


def restore_original_path_in_error(
    error: Exception, temp_path: Path, original_path: Path
) -> None:
    """
    Replace occurrences of a temporary path in an exception's traceback with the original path.

    This ensures that error messages and traceback outputs display the correct path.

    :param error: The original exception raised.
    :type error: Exception
    :param temp_path: The temporary path to be replaced.
    :type temp_path: str
    :param original_path: The original path to replace it with.
    :type original_path: str
    :raises Exception: The original exception with an adjusted traceback (printed separately).
    """
    # Format and modify the traceback
    tb_list = traceback.format_exception(type(error), error, error.__traceback__)
    tb_modified = [line.replace(str(temp_path), str(original_path)) for line in tb_list]

    # Log the modified traceback
    logger.error("".join(tb_modified), stack_info=False)

    # Exit the program to suppress the default traceback output
    raise error.with_traceback(error.__traceback__)
