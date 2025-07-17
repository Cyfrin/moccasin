import boa
import pytest
from eth_account import Account
from eth_utils import to_wei
from script.deploy_dsc_engine import deploy_dsc_engine

from moccasin.config import get_active_network

BALANCE = to_wei(10, "ether")
COLLATERAL_AMOUNT = to_wei(10, "ether")
AMOUNT_TO_MINT = to_wei(100, "ether")
COLLATERAL_TO_COVER = to_wei(20, "ether")


# ------------------------------------------------------------------
#                         SESSION SCOPED
# ------------------------------------------------------------------
@pytest.fixture(scope="session")
def active_network():
    return get_active_network()


@pytest.fixture(scope="session")
def weth(active_network):
    return active_network.manifest_named("weth")


@pytest.fixture(scope="session")
def wbtc(active_network):
    return active_network.manifest_named("wbtc")


@pytest.fixture(scope="session")
def eth_usd(active_network):
    return active_network.manifest_named("eth_usd_price_feed")


@pytest.fixture(scope="session")
def btc_usd(active_network):
    return active_network.manifest_named("btc_usd_price_feed")


@pytest.fixture(scope="session")
def some_user(weth, wbtc):
    entropy = 13
    account = Account.create(entropy)
    boa.env.set_balance(account.address, BALANCE)
    with boa.env.prank(account.address):
        weth.mock_mint()
        wbtc.mock_mint()
    return account.address


@pytest.fixture(scope="session")
def liquidator(weth, wbtc):
    entropy = 234
    account = Account.create(entropy)
    boa.env.set_balance(account.address, BALANCE)
    with boa.env.prank(account.address):
        weth.mock_mint()
        wbtc.mock_mint()
    return account.address


# ------------------------------------------------------------------
#                        FUNCTION SCOPED
# ------------------------------------------------------------------
@pytest.fixture
def dsc(active_network):
    return active_network.manifest_named("decentralized_stable_coin")


@pytest.fixture
def dsce(dsc, weth, wbtc, eth_usd, btc_usd):
    return deploy_dsc_engine(dsc)


@pytest.fixture
def dsce_deposited(dsce, some_user, weth):
    with boa.env.prank(some_user):
        weth.approve(dsce.address, COLLATERAL_AMOUNT)
        dsce.deposit_collateral(weth.address, COLLATERAL_AMOUNT)
    return dsce


@pytest.fixture
def dsce_minted(dsce, some_user, weth):
    with boa.env.prank(some_user):
        weth.approve(dsce.address, COLLATERAL_AMOUNT)
        dsce.deposit_collateral_and_mint_dsc(
            weth.address, COLLATERAL_AMOUNT, AMOUNT_TO_MINT
        )
    return dsce


@pytest.fixture
def starting_liquidator_weth_balance(liquidator, weth):
    return weth.balanceOf(liquidator)


@pytest.fixture
def dsce_liquidated(
    starting_liquidator_weth_balance,
    dsce_minted,
    weth,
    dsc,
    some_user,
    liquidator,
    eth_usd,
):
    weth.mock_mint()

    eth_usd_updated_price = 18 * 10**8  # 1 ETH = $18
    eth_usd.updateAnswer(eth_usd_updated_price)

    with boa.env.prank(liquidator):
        weth.mock_mint()
        weth.approve(dsce_minted, COLLATERAL_TO_COVER)
        dsce_minted.deposit_collateral_and_mint_dsc(
            weth, COLLATERAL_TO_COVER, AMOUNT_TO_MINT
        )
        dsc.approve(dsce_minted, AMOUNT_TO_MINT)
        dsce_minted.liquidate(weth, some_user, AMOUNT_TO_MINT)

    return dsce_minted
