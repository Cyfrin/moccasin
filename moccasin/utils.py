from typing import Tuple


def get_int_bounds(type_str: str) -> Tuple[int, int]:
    """Returns the lower and upper bound for an integer type."""
    size = int(type_str.strip("uint") or 256)
    if size < 8 or size > 256 or size % 8:
        raise ValueError(f"Invalid type: {type_str}")
    if type_str.startswith("u"):
        return 0, 2**size - 1
    return -(2 ** (size - 1)), 2 ** (size - 1) - 1