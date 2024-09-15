def test_using_fixture_one(price_feed):
    assert price_feed.address is not None


def test_using_fixture_two(price_feed, eth_usd):
    assert price_feed.address is not None
    assert eth_usd.address is not None
