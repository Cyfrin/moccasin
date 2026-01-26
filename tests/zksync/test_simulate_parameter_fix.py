"""
Tests for the ZksyncEnv.execute_code 'simulate' parameter fix.

This test file verifies the fix for GitHub issue #271:
https://github.com/Cyfrin/moccasin/issues/271

The issue: titanoboa >= 0.2.6 passes a 'simulate' parameter to execute_code(),
but ZksyncEnv.execute_code() didn't accept it, causing TypeError when calling
contract functions after deployment.

The fix: Monkey patch in moccasin/config.py that wraps ZksyncEnv.execute_code
to accept the 'simulate' parameter.
"""

import inspect

import pytest

# Import config first to apply the monkey patch
from moccasin.config import Network  # noqa: F401
from boa_zksync.environment import ZksyncEnv


def test_zksync_env_execute_code_accepts_simulate_parameter():
    """
    Verify ZksyncEnv.execute_code accepts the 'simulate' parameter.

    COMMENT: This test verifies the monkey patch was applied correctly.
    The 'simulate' parameter must be present to accept calls from titanoboa >= 0.2.6
    """
    sig = inspect.signature(ZksyncEnv.execute_code)

    # COMMENT: Check that 'simulate' is in the method signature
    assert "simulate" in sig.parameters, (
        "ZksyncEnv.execute_code must accept 'simulate' parameter "
        "to be compatible with titanoboa >= 0.2.6"
    )

    # COMMENT: Verify it has a default value of False for backward compatibility
    assert sig.parameters["simulate"].default is False


def test_zksync_env_execute_code_backward_compatible():
    """
    Test that execute_code works WITHOUT the simulate parameter.

    COMMENT: Ensures backward compatibility - existing code that doesn't
    pass 'simulate' should still work.
    """
    sig = inspect.signature(ZksyncEnv.execute_code)

    # COMMENT: Try binding without simulate parameter - should work
    try:
        sig.bind_partial(None, to_address="0x" + "00" * 20, data=b"")
    except TypeError as e:
        pytest.fail(f"Backward compatibility broken: {e}")


def test_zksync_env_execute_code_accepts_simulate_false():
    """
    Test that execute_code accepts simulate=False.

    COMMENT: This is the exact call pattern from titanoboa >= 0.2.6
    that was failing before the fix.
    """
    sig = inspect.signature(ZksyncEnv.execute_code)

    # COMMENT: Try binding WITH simulate=False - this is what titanoboa does
    # Before the fix, this would raise: TypeError: unexpected keyword argument 'simulate'
    try:
        sig.bind_partial(None, to_address="0x" + "00" * 20, data=b"", simulate=False)
    except TypeError as e:
        pytest.fail(f"Cannot accept simulate=False: {e}")


def test_zksync_env_execute_code_accepts_simulate_true():
    """
    Test that execute_code accepts simulate=True.

    COMMENT: Full parameter support verification.
    """
    sig = inspect.signature(ZksyncEnv.execute_code)

    # COMMENT: Try binding WITH simulate=True
    try:
        sig.bind_partial(None, to_address="0x" + "00" * 20, data=b"", simulate=True)
    except TypeError as e:
        pytest.fail(f"Cannot accept simulate=True: {e}")


# -----------------------------------------------------------------------------
# Integration Tests - Require anvil-zksync
# -----------------------------------------------------------------------------

def test_deploy_and_call_contract_function(
    zksync_cleanup_out_folder, zk_temp_path, zksync_test_env
):
    """
    Integration test: Deploy contract and call its function.

    This is the EXACT scenario from issue #271:
    1. Deploy contract (works)
    2. Call contract function (was failing with TypeError about 'simulate')

    COMMENT: This test reproduces the bug and verifies the fix works end-to-end.
    Before the fix, the get_difficulty() call would raise:
    TypeError: ZksyncEnv.execute_code() got an unexpected keyword argument 'simulate'
    """
    from moccasin.commands.run import run_script

    # COMMENT: Deploy the contract using deployment script
    difficulty_contract = run_script(zk_temp_path.joinpath("script/deploy.py"))

    # COMMENT: Call a view function - this is where the bug occurred
    # titanoboa internally calls execute_code with simulate=False
    difficulty = difficulty_contract.get_difficulty()

    # COMMENT: If we got here without TypeError, the fix works!
    assert difficulty == 2500000000000000


def test_multiple_function_calls(
    zksync_cleanup_out_folder, zk_temp_path, zksync_test_env
):
    """
    Integration test: Multiple sequential function calls.

    COMMENT: Ensures the fix works for repeated calls, not just once.
    """
    from moccasin.commands.run import run_script

    difficulty_contract = run_script(zk_temp_path.joinpath("script/deploy.py"))

    # COMMENT: Make multiple calls - each goes through execute_code with simulate parameter
    for _ in range(3):
        difficulty = difficulty_contract.get_difficulty()
        assert difficulty == 2500000000000000


def test_boa_load_pattern(
    zksync_cleanup_out_folder, zk_temp_path, zksync_test_env
):
    """
    Integration test: Deploy via boa.load() and call functions.

    COMMENT: Tests the boa.load() pattern mentioned in issue #271.
    """
    import boa

    # COMMENT: Deploy using boa.load() - pattern from the issue
    difficulty_contract = boa.load(zk_temp_path.joinpath("src/Difficulty.vy"))

    # COMMENT: Call function - TypeError would occur here before the fix
    difficulty = difficulty_contract.get_difficulty()

    assert difficulty == 2500000000000000
