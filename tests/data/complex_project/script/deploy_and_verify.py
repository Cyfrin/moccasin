from contracts import Counter

from moccasin.config import get_active_network


def moccasin_main():
    active_network = get_active_network()
    counter = Counter.deploy()
    print("Counter deployed at", counter.address)
    result = active_network.moccasin_verify(counter)
    result.wait_for_verification()
    print("Counter verified")
