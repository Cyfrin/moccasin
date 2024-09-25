from moccasin.config import get_config


def test_increment(counter_contract):
    breakpoint()
    counter_contract.increment()
    assert counter_contract.number() == 2
