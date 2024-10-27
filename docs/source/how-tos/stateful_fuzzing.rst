Stateful Fuzzing 
#################

.. important:: 

    Be sure to read the :doc:`fuzzing </core_concepts/testing/fuzzing>` guide before reading this one.


Example Contract 
================

Let's say we have the following contract:

.. code-block:: python 

    """
    @ pragma version 0.4.0
    @ title always_return_input_two
    @ license MIT
    @ notice INVARIANT: always_returns_input_number should always return the input number
    """
    some_number: public(uint256)

    @external
    def always_returns_input_number(input_number: uint256) -> uint256:
        """
        @param input_number The input number to check
        """
        if self.some_number == 2:
            return 0
        return input_number

    @external 
    def change_number(new_number: uint256):
        self.some_number = new_number

The `invariant` in this contract is that the function `always_returns_input_number` should always return the input number. But as we can see from looking at the function, we notice that if someone were to call ``change_number`` with an input of ``2``, the ``always_returns_input_number`` function will return 0 no matter what. 

This is easy for us to "see", but when contracts get sufficiently complicated, spotting these kinds of bugs becomes harder and harder, and this is where our tests come in. 

Stateful Fuzz Testing
=====================

To fuzz test this, in ``moccasin`` we'd create a new file in our ``tests`` directory like so:

.. code-block:: python 

    from hypothesis.stateful import RuleBasedStateMachine, rule
    from hypothesis import settings
    from contracts.sub_lesson import stateful_fuzz_solvable
    from boa.test.strategies import strategy


    class StatefulFuzzer(RuleBasedStateMachine):
        def __init__(self):
            super().__init__()
            self.contract = stateful_fuzz_solvable.deploy()

        @rule(new_number=strategy("uint256"))
        def change_number(self, new_number):
            self.contract.change_number(new_number)

        # ------------------------------------------------------------------
        #                           INVARIANTS
        # ------------------------------------------------------------------
        @rule(input_number=strategy("uint256"))
        def input_number_returns_itself(self, input_number):
            print(input_number)
            result = int(self.contract.always_returns_input_number(input_number))
            assert result == input_number, f"Expected {input_number}, got {result}"


    TestStatefulFuzzing = StatefulFuzzer.TestCase
    TestStatefulFuzzing.settings = settings(max_examples=10000, stateful_step_count=50)

Essentially, what this will try to do will be:

1. Start a "fuzz run"
    a. It will deploy a our contract 
    b. It will randomly call either ``input_number_returns_itself`` or ``change_number`` with random inputs `on the same contract`
    c. The ``input_number_returns_itself`` function always checks our invariant 
2. After ``stateful_step_count`` "fuzz runs" (50, in this case) it will stop, and "delete" our contract 
3. It will repeat step 1 in this list until it finds an issue, or runs through these steps ``max_examples`` (10,000 in our example) times!

You can then test it with:

.. code-block:: bash 

    mox test 


And you'll see an output like:

.. code-block:: bash 

    >       assert result == input_number, f"Expected {input_number}, got {result}"
    E       AssertionError: Expected 1, got 0
    E       Falsifying example:
    E       state = StatefulFuzzer()
    E       state.change_number(new_number=2)
    E       state.input_number_returns_itself(input_number=1)
    E       state.teardown()

This means, it found a bug! It first called ``change_number`` and set it to 2, and then called ``input_number_returns_itself`` with 1, but it returned 0 instead of 1!