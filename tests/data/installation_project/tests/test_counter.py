def test_increment(counter_contract):
    counter_contract.increment()
    assert counter_contract.number() == 2