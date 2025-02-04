import boa
from boa import Env

from moccasin.moccasin_account import MoccasinAccount
from tests.constants import ANVIL1_PRIVATE_KEY

STARTING_ANVIL1_BALANCE = 10000000000000000000000


def test_get_balance_env(anvil_two_no_state, complex_project_config):
    network = "anvil-fork"  # Not a real fork
    complex_project_config.set_active_network(network)
    mox_account = MoccasinAccount(private_key=ANVIL1_PRIVATE_KEY)
    assert mox_account.get_balance() >= STARTING_ANVIL1_BALANCE
    # We should do this more places to make tests more isolated.
    boa.set_env(Env())


def test_get_balance_no_env():
    mox_account = MoccasinAccount(private_key=ANVIL1_PRIVATE_KEY)
    assert mox_account.get_balance() == 0
