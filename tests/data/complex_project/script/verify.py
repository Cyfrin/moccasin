import os

import boa
from boa.verifiers import Blockscout
from contracts import Counter


def moccasin_main():
    counter = Counter.at("0x64A5F381A9D4eBA6d6A7D24De4D799901B19d29d")
    api_key = os.getenv("BLOCKSCOUT_API_KEY")
    blockscout = Blockscout("https://eth-sepolia.blockscout.com", api_key)
    with boa.set_verifier(blockscout):
        result = boa.verify(counter)
        result.wait_for_verification()
        assert result.is_verified()
