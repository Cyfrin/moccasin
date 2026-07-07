import subprocess

import pytest


EXPECTED_ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.mark.parametrize(
    "utils_command",
    ["zero", "zero-address", "zero_address", "address-zero", "address_zero"],
)
def test_utils_zero_aliases(mox_path, utils_command):
    result = subprocess.run(
        [mox_path, "utils", utils_command],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == EXPECTED_ZERO_ADDRESS
    assert result.returncode == 0


@pytest.mark.parametrize("utils_alias", ["u", "util"])
def test_utils_command_aliases(mox_path, utils_alias):
    result = subprocess.run(
        [mox_path, utils_alias, "zero"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == EXPECTED_ZERO_ADDRESS
    assert result.returncode == 0
