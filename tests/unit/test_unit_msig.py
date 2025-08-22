import pytest
from prompt_toolkit import PromptSession

from moccasin.msig_cli.validators import (
    is_not_empty,
    is_valid_address,
    is_valid_boolean,
    is_valid_data,
    is_valid_function_signature,
    is_valid_not_zero_number,
    is_valid_number,
    is_valid_operation,
    is_valid_rpc_url,
    is_valid_tx_build_data_type,
    validator_address,
    validator_boolean,
    validator_data,
    validator_empty_or_function_signature,
    validator_not_empty,
    validator_number,
    validator_empty_or_operation,
    validator_rpc_url,
    validator_empty_or_tx_build_data_type,
)


def test_prompt_example(pt_session):
    pt_session.send_text("hello\n")
    session = PromptSession(input=pt_session)
    assert session.prompt("Say hi: ") == "hello"


# --- msig.py validator tests ---
def test_is_valid_address():
    assert is_valid_address("0x1234567890abcdef1234567890abcdef12345678")
    assert not is_valid_address("0x1234")
    assert not is_valid_address("")


def test_is_valid_rpc_url():
    assert is_valid_rpc_url("http://localhost:8545")
    assert is_valid_rpc_url("https://mainnet.infura.io/v3/xxx")
    assert not is_valid_rpc_url("ftp://example.com")
    assert not is_valid_rpc_url("")


def test_is_valid_number():
    assert is_valid_number("0")
    assert is_valid_number("123")
    assert not is_valid_number("-1")
    assert not is_valid_number("abc")
    assert not is_valid_number("")


def test_is_valid_not_zero_number():
    assert is_valid_not_zero_number("1")
    assert is_valid_not_zero_number("100")
    assert not is_valid_not_zero_number("0")
    assert not is_valid_not_zero_number("-1")
    assert not is_valid_not_zero_number("abc")
    assert not is_valid_not_zero_number("")


def test_is_valid_operation():
    assert is_valid_operation("0")
    assert is_valid_operation("1")
    assert not is_valid_operation("2")
    assert not is_valid_operation("-1")
    assert not is_valid_operation("abc")
    assert not is_valid_operation("")


def test_is_valid_data():
    assert is_valid_data("0x1234")
    assert is_valid_data("0x")
    assert not is_valid_data("1234")
    assert not is_valid_data("")


def test_is_valid_transaction_type():
    assert is_valid_tx_build_data_type("0")
    assert is_valid_tx_build_data_type("1")
    assert not is_valid_tx_build_data_type("2")
    assert not is_valid_tx_build_data_type("3")
    assert not is_valid_tx_build_data_type("-1")
    assert not is_valid_tx_build_data_type("abc")
    assert not is_valid_tx_build_data_type("")


def test_is_valid_function_signature():
    assert is_valid_function_signature("transfer(address,uint256)")
    assert is_valid_function_signature("approve(address,uint256)")
    assert not is_valid_function_signature("not_a_function")
    assert not is_valid_function_signature("")


def test_is_valid_boolean():
    assert is_valid_boolean("true")
    assert is_valid_boolean("false")
    assert not is_valid_boolean("yes")
    assert not is_valid_boolean("0")
    assert not is_valid_boolean("")


def test_is_not_empty():
    assert is_not_empty("something")
    assert not is_not_empty("")


# --- Parametrized prompt_toolkit validator tests (valid input only) ---
def _prompt_with_validator(session, prompt_text, validator):
    """Prompt with a validator using prompt_toolkit.

    prompt_toolkit will keep prompting until valid input is given.
    @dev Each `\n` in pt_session.send_text() simulates the user pressing Enter
    after typing an input.

    Example

    "notanaddress\n0x1234...5678\n" means:
        - First input: notanaddress (invalid, prompt_toolkit re-prompts)
        - Second input: 0x1234...5678 (valid, accepted)
    """
    return session.prompt(prompt_text, validator=validator)


@pytest.mark.parametrize(
    "prompt_text,validator,input_value,expected",
    [
        (
            "Address: ",
            validator_address,
            "0x1234567890abcdef1234567890abcdef12345678",
            "0x1234567890abcdef1234567890abcdef12345678",
        ),
        (
            "RPC URL: ",
            validator_rpc_url,
            "https://mainnet.infura.io/v3/xxx",
            "https://mainnet.infura.io/v3/xxx",
        ),
        ("Number: ", validator_number, "42", "42"),
        ("Boolean: ", validator_boolean, "true", "true"),
        ("Boolean: ", validator_boolean, "false", "false"),
        ("Operation: ", validator_empty_or_operation, "0", "0"),
        (
            "Data: ",
            validator_data,
            "0xa9059cbb000000000000000000000000cfaacfc01548da1478432cf3abdcd1cbdff11e1c000000000000000000000000000000000000000000000000000000000000002a",
            "0xa9059cbb000000000000000000000000cfaacfc01548da1478432cf3abdcd1cbdff11e1c000000000000000000000000000000000000000000000000000000000000002a",
        ),
        (
            "Transaction Building Data Type: ",
            validator_empty_or_tx_build_data_type,
            "1",
            "1",
        ),
        (
            "Function Signature: ",
            validator_empty_or_function_signature,
            "transfer(address,uint256)",
            "transfer(address,uint256)",
        ),
        ("Not Empty: ", validator_not_empty, "something", "something"),
    ],
)
def test_prompt_valid_inputs(pt_session, prompt_text, validator, input_value, expected):
    """
    Test prompt_toolkit validators with valid input only.
    Note: Invalid input cases are not included here, as prompt_toolkit will hang waiting for valid input.
    """
    pt_session.send_text(f"{input_value}\n")
    session = PromptSession(input=pt_session)
    result = _prompt_with_validator(session, prompt_text, validator)
    assert result == expected
