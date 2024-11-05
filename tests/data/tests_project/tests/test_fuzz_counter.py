from boa.test.strategies import strategy
from hypothesis import assume, settings
from hypothesis.stateful import RuleBasedStateMachine, initialize, rule
from script.deploy import deploy

MAX_UINT256 = 2**256 - 1


class CounterFuzzer(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()

    @initialize()
    def setup(self):
        self.counter = deploy()
        self.number = self.counter.number()

    @rule(amount=strategy("uint256"))
    def set_number(self, amount):
        self.counter.set_number(amount)

    @rule()
    def increment(self):
        assume(self.counter.number() < MAX_UINT256)
        self.counter.increment()

    # # This should break!
    # @invariant()
    # def number_goes_up(self):
    #     new_number = self.counter.number()
    #     assert new_number >= self.number
    #     self.number = new_number


fuzzer = CounterFuzzer.TestCase
fuzzer.settings = settings(max_examples=64, stateful_step_count=64, print_blob=True)
