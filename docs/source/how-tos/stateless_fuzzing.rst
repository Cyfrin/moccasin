Stateless Fuzzing 
#################

.. important:: 

    Be sure to read the :doc:`fuzzing </core_concepts/testing/fuzzing>` guide before reading this one.


Example Contract 
================

Let's say you have a contract as such:

.. code-block:: python

    """
    @ pragma version 0.4.0
    @ title always_return_input
    @ license MIT
    @ notice INVARIANT: always_returns_input_number should always return the input number
    """

    @external
    @pure
    def always_returns_input_number(input_number: uint256) -> uint256:
        """
        @param input_number The input number to check
        """
        if input_number == 2:
            return 0
        return input_number

The `invariant` in this contract is that the function `always_returns_input_number` should always return the input number. But as we can see from looking at the function, we notice that if the input number is 2, the function will return 0. 

This is easy for us to "see", but when contracts get sufficiently complicated, spotting these kinds of bugs becomes harder and harder, and this is where our tests come in. 

Stateless Fuzz Testing
======================

To fuzz test this, in ``moccasin`` we'd create a new file in our ``tests`` directory like so:

.. code-block:: python 

    # Assuming the contract is named `stateless_fuzz_solvable` in the `contracts.sub_lesson` folder
    from contracts.sub_lesson import stateless_fuzz_solvable
    from hypothesis import given, settings
    from boa.test.strategies import strategy

    @settings(max_examples=1000)
    @given(input_number=strategy("uint256"))
    def test_always_returns_input_number_property_any_bounds(contract, input_number):
        """
        Property test to verify the core behavior of always_returns_input_number
        """
        contract = stateless_fuzz_solvable.deploy()
        result = int(contract.always_returns_input_number(input_number))
        assert result == input_number, f"Expected {input_number}, got {result}"

Essentially, what this will try to do will be:

1. It will deploy a our contract 
2. It will call the `always_returns_input_number` function with a random `uint256` input
3. It will check if the result is the same as the input number

It will continue to do this for 1,000 "fuzz runs", which means 1,000 different random numbers. You can then test it with:

.. code-block:: bash 

    mox test 


And you'll see an output like:

.. code-block:: bash 

    >       assert result == input_number, f"Expected {input_number}, got {result}"
    E       AssertionError: Expected 2, got 0
    E       Falsifying example: f(
    E           contract=<~/code/vyper-full-course-cu-2/12-mox-erc20-cu/contracts/sub_lesson/stateless_fuzz_solvable.vy at 0xC6Acb7D16D51f72eAA659668F30A40d87E2E0551, compiled with vyper-0.4.0+e9db8d9>,
    E           input_number=2,
    E       )

This means, it found a bug! When ``input_number=2``, the function returns 0, which is not what we expect!