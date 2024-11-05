def test_counter(counter_contract):
    assert counter_contract.number() == 1
