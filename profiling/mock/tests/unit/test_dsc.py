import boa

ZERO = "0x0000000000000000000000000000000000000000"


def test_cannot_mint_to_zero_address(dsc):
    with boa.env.prank(dsc.owner()):
        with boa.reverts():
            dsc.mint(ZERO, 0)


def test_cant_burn_more_than_you_have(dsc):
    with boa.env.prank(dsc.owner()):
        with boa.reverts():
            dsc.burn_from(dsc.owner(), 1)


# Can you think of more?
