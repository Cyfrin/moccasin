import boa
import pytest
from eth.codecs.abi.exceptions import EncodeError
from eth_utils import to_wei
from script.mocks.deploy_collateral import deploy_collateral
from src import dsc_engine
from src.mocks import mock_more_debt_dsc

from tests.conftest import AMOUNT_TO_MINT, COLLATERAL_AMOUNT, COLLATERAL_TO_COVER

MIN_HEALTH_FACTOR = to_wei(1, "ether")
LIQUIDATION_THRESHOLD = 50


# ------------------------------------------------------------------
#                       CONSTRUCTOR TESTS
# ------------------------------------------------------------------
def test_reverts_if_token_length_doesnt_match_price_feeds(
    dsc, eth_usd, btc_usd, weth, wbtc
):
    with pytest.raises(EncodeError):
        dsc_engine.deploy([wbtc, weth, weth], [eth_usd, btc_usd], dsc)


# ------------------------------------------------------------------
#                          PRICE TESTS
# ------------------------------------------------------------------
def test_get_token_amount_from_usd(dsce, weth):
    expected_weth = to_wei(0.05, "ether")
    actual_weth = dsce.get_token_amount_from_usd(weth, to_wei(100, "ether"))
    assert expected_weth == actual_weth


def test_get_usd_value(dsce, weth):
    eth_amount = to_wei(15, "ether")
    expected_usd = to_wei(30_000, "ether")
    actual_usd = dsce.get_usd_value(weth, eth_amount)
    assert expected_usd == actual_usd


# ------------------------------------------------------------------
#                       DEPOSITCOLLATERAL
# ------------------------------------------------------------------
def test_reverts_if_collateral_zero(some_user, weth, dsce):
    with boa.env.prank(some_user):
        weth.approve(dsce, COLLATERAL_AMOUNT)
        with boa.reverts():
            dsce.deposit_collateral(weth, 0)


def test_reverts_with_unapproved_collateral(some_user, dsce):
    random_collateral = deploy_collateral()
    with boa.env.prank(some_user):
        random_collateral.mock_mint()
        with boa.reverts("DSCEngine__TokenNotAllowed"):
            random_collateral.approve(dsce, COLLATERAL_AMOUNT)
            dsce.deposit_collateral(random_collateral, COLLATERAL_AMOUNT)


def test_can_deposit_collateral_without_minting(dsce_deposited, dsc, some_user):
    assert dsc.balanceOf(some_user) == 0


def test_can_deposit_collateral_and_get_account_info(dsce_deposited, some_user, weth):
    dsc_minted, collateral_value_usd = dsce_deposited.get_account_information(some_user)
    expected_deposit_amount = dsce_deposited.get_token_amount_from_usd(
        weth, collateral_value_usd
    )
    assert dsc_minted == 0
    assert expected_deposit_amount == COLLATERAL_AMOUNT


# ------------------------------------------------------------------
#               DEPOSIT COLLATERAL AND MINT DSC TESTS
# ------------------------------------------------------------------
def test_reverts_if_minted_dsc_breaks_health_factor(dsce, weth, eth_usd, some_user):
    price = eth_usd.latestRoundData()[1]
    amount_to_mint = (
        COLLATERAL_AMOUNT * (price * dsce.ADDITIONAL_FEED_PRECISION())
    ) // dsce.PRECISION()

    with boa.env.prank(some_user):
        weth.approve(dsce, COLLATERAL_AMOUNT)
        dsce.calculate_health_factor(
            amount_to_mint, dsce.get_usd_value(weth, COLLATERAL_AMOUNT)
        )
        with boa.reverts("DSCEngine__BreaksHealthFactor"):
            dsce.deposit_collateral_and_mint_dsc(
                weth, COLLATERAL_AMOUNT, amount_to_mint
            )


def test_can_mint_with_deposited_collateral(dsce_minted, dsc, some_user):
    user_balance = dsc.balanceOf(some_user)
    assert user_balance == AMOUNT_TO_MINT


# ------------------------------------------------------------------
#                          MINT DSC TESTS
# ------------------------------------------------------------------
def test_reverts_if_mint_amount_breaks_health_factor(
    dsce_deposited, eth_usd, some_user, weth
):
    price = eth_usd.latestRoundData()[1]
    amount_to_mint = (
        COLLATERAL_AMOUNT * (price * dsce_deposited.ADDITIONAL_FEED_PRECISION())
    ) // dsce_deposited.PRECISION()

    with boa.env.prank(some_user):
        dsce_deposited.calculate_health_factor(
            amount_to_mint, dsce_deposited.get_usd_value(weth, COLLATERAL_AMOUNT)
        )
        with boa.reverts("DSCEngine__BreaksHealthFactor"):
            dsce_deposited.mint_dsc(amount_to_mint)


def test_can_mint_dsc(dsce_deposited, dsc, some_user):
    with boa.env.prank(some_user):
        dsce_deposited.mint_dsc(AMOUNT_TO_MINT)
        user_balance = dsc.balanceOf(some_user)
        assert user_balance == AMOUNT_TO_MINT


# ------------------------------------------------------------------
#                          BURN DSC TESTS
# ------------------------------------------------------------------
def test_cant_burn_more_than_user_has(dsce, dsc, some_user):
    with boa.env.prank(some_user):
        dsc.approve(dsce, 1)
        with boa.reverts():
            dsce.burn_dsc(1)


def test_can_burn_dsc(dsce_minted, dsc, some_user):
    with boa.env.prank(some_user):
        dsc.approve(dsce_minted, AMOUNT_TO_MINT)
        dsce_minted.burn_dsc(AMOUNT_TO_MINT)
        user_balance = dsc.balanceOf(some_user)
        assert user_balance == 0


# ------------------------------------------------------------------
#                     REDEEM COLLATERAL TESTS
# ------------------------------------------------------------------
def test_can_redeem_collateral(dsce, weth, dsc, some_user):
    with boa.env.prank(some_user):
        weth.approve(dsce, COLLATERAL_AMOUNT)
        dsc.approve(dsce, AMOUNT_TO_MINT)
        dsce.deposit_collateral_and_mint_dsc(weth, COLLATERAL_AMOUNT, AMOUNT_TO_MINT)
        dsce.redeem_collateral_for_dsc(weth, COLLATERAL_AMOUNT, AMOUNT_TO_MINT)
        user_balance = dsc.balanceOf(some_user)
        assert user_balance == 0


def test_properly_reports_health_factor(dsce_minted, some_user):
    expected_health_factor = to_wei(100, "ether")
    actual_health_factor = dsce_minted.health_factor(some_user)
    assert expected_health_factor == actual_health_factor


def test_health_factor_can_go_below_one(dsce_minted, eth_usd, some_user):
    eth_usd_updated_price = 18 * 10**8
    eth_usd.updateAnswer(eth_usd_updated_price)
    user_health_factor = dsce_minted.health_factor(some_user)
    assert user_health_factor == to_wei(0.9, "ether")


# ------------------------------------------------------------------
#                     LIQUIDATION TESTS
# ------------------------------------------------------------------
def test_must_improve_health_factor_on_liquidation(
    some_user, liquidator, weth, eth_usd, wbtc, btc_usd
):
    # Setup mock DSC
    mock_dsc = mock_more_debt_dsc.deploy(eth_usd)
    token_addresses = [weth, wbtc]
    feed_addresses = [eth_usd, btc_usd]
    dsce = dsc_engine.deploy(token_addresses, feed_addresses, mock_dsc)
    mock_dsc.set_minter(dsce.address, True)
    mock_dsc.transfer_ownership(dsce)

    # Setup user position
    with boa.env.prank(some_user):
        weth.approve(dsce, COLLATERAL_AMOUNT)
        dsce.deposit_collateral_and_mint_dsc(weth, COLLATERAL_AMOUNT, AMOUNT_TO_MINT)

    # Setup liquidator
    collateral_to_cover = to_wei(1, "ether")
    weth.mint(liquidator, collateral_to_cover)

    with boa.env.prank(liquidator):
        weth.approve(dsce, collateral_to_cover)
        debt_to_cover = to_wei(10, "ether")
        dsce.deposit_collateral_and_mint_dsc(weth, collateral_to_cover, AMOUNT_TO_MINT)
        mock_dsc.approve(dsce, debt_to_cover)

        # Update price to trigger liquidation
        eth_usd_updated_price = 18 * 10**8  # 1 ETH = $18
        eth_usd.updateAnswer(eth_usd_updated_price)

        with boa.reverts("DSCEngine__HealthFactorNotImproved"):
            dsce.liquidate(weth, some_user, debt_to_cover)


def test_cant_liquidate_good_health_factor(
    dsce_minted, weth, dsc, some_user, liquidator
):
    weth.mint(liquidator, COLLATERAL_TO_COVER)

    with boa.env.prank(liquidator):
        weth.approve(dsce_minted, COLLATERAL_TO_COVER)
        dsce_minted.deposit_collateral_and_mint_dsc(
            weth, COLLATERAL_TO_COVER, AMOUNT_TO_MINT
        )
        dsc.approve(dsce_minted, AMOUNT_TO_MINT)

        with boa.reverts("DSCEngine__HealthFactorOk"):
            dsce_minted.liquidate(weth, some_user, AMOUNT_TO_MINT)


def test_liquidation_payout_is_correct(
    starting_liquidator_weth_balance, dsce_liquidated, weth, liquidator
):
    liquidator_weth_balance = weth.balanceOf(liquidator)

    expected_weth = dsce_liquidated.get_token_amount_from_usd(weth, AMOUNT_TO_MINT) + (
        dsce_liquidated.get_token_amount_from_usd(weth, AMOUNT_TO_MINT)
        // dsce_liquidated.LIQUIDATION_BONUS()
    )
    hard_coded_expected = 6_111_111_111_111_111_110
    assert liquidator_weth_balance == hard_coded_expected
    assert liquidator_weth_balance == expected_weth


def test_user_still_has_some_eth_after_liquidation(dsce_liquidated, weth, some_user):
    amount_liquidated = dsce_liquidated.get_token_amount_from_usd(
        weth, AMOUNT_TO_MINT
    ) + (
        dsce_liquidated.get_token_amount_from_usd(weth, AMOUNT_TO_MINT)
        // dsce_liquidated.LIQUIDATION_BONUS()
    )

    usd_amount_liquidated = dsce_liquidated.get_usd_value(weth, amount_liquidated)
    expected_user_collateral_value_in_usd = (
        dsce_liquidated.get_usd_value(weth, COLLATERAL_AMOUNT) - usd_amount_liquidated
    )

    _, user_collateral_value_in_usd = dsce_liquidated.get_account_information(some_user)
    hard_coded_expected_value = 70_000_000_000_000_000_020
    assert user_collateral_value_in_usd == expected_user_collateral_value_in_usd
    assert user_collateral_value_in_usd == hard_coded_expected_value


def test_liquidator_takes_on_users_debt(dsce_liquidated, liquidator):
    liquidator_dsc_minted, _ = dsce_liquidated.get_account_information(liquidator)
    assert liquidator_dsc_minted == AMOUNT_TO_MINT


def test_user_has_no_more_debt(dsce_liquidated, some_user):
    user_dsc_minted, _ = dsce_liquidated.get_account_information(some_user)
    assert user_dsc_minted == 0


# ------------------------------------------------------------------
#                    VIEW & PURE FUNCTION TESTS
# ------------------------------------------------------------------
def test_get_collateral_token_price_feed(dsce, weth, eth_usd):
    price_feed = dsce.token_address_to_price_feed(weth)
    assert price_feed == eth_usd.address


def test_get_collateral_tokens(dsce, weth):
    collateral_tokens = dsce.get_collateral_tokens()
    assert collateral_tokens[1] == weth.address


def test_get_min_health_factor(dsce):
    min_health_factor = dsce.MIN_HEALTH_FACTOR()
    assert min_health_factor == MIN_HEALTH_FACTOR


def test_get_liquidation_threshold(dsce):
    liquidation_threshold = dsce.LIQUIDATION_THRESHOLD()
    assert liquidation_threshold == LIQUIDATION_THRESHOLD


def test_get_account_collateral_value_from_information(dsce_deposited, some_user, weth):
    _, collateral_value = dsce_deposited.get_account_information(some_user)
    expected_collateral_value = dsce_deposited.get_usd_value(weth, COLLATERAL_AMOUNT)
    assert collateral_value == expected_collateral_value


def test_get_collateral_balance_of_user(dsce, weth, some_user):
    with boa.env.prank(some_user):
        weth.approve(dsce, COLLATERAL_AMOUNT)
        dsce.deposit_collateral(weth, COLLATERAL_AMOUNT)

    collateral_balance = dsce.get_collateral_balance_of_user(some_user, weth)
    assert collateral_balance == COLLATERAL_AMOUNT


def test_get_account_collateral_value(dsce, weth, some_user):
    with boa.env.prank(some_user):
        weth.approve(dsce, COLLATERAL_AMOUNT)
        dsce.deposit_collateral(weth, COLLATERAL_AMOUNT)

    collateral_value = dsce.get_account_collateral_value(some_user)
    expected_collateral_value = dsce.get_usd_value(weth, COLLATERAL_AMOUNT)
    assert collateral_value == expected_collateral_value


def test_get_dsc(dsce, dsc):
    dsc_address = dsce.DSC()
    assert dsc_address == dsc.address


def test_liquidation_precision(dsce):
    expected_liquidation_precision = 100
    actual_liquidation_precision = dsce.LIQUIDATION_PRECISION()
    assert actual_liquidation_precision == expected_liquidation_precision
