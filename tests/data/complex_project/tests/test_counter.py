def test_increment_one(counter_contract):
    counter_contract.increment()
    assert counter_contract.number() == 2


def test_increment_two(counter_contract):
    counter_contract.increment()
    counter_contract.increment()
    assert counter_contract.number() == 3
