Fuzzing 
#######

In ``moccasin``, we use `hypothesis <https://hypothesis.readthedocs.io/en/latest/quickstart.html>`_ for fuzz testing. Moccasin has some built-in functions for working with stateful and stateless fuzzing.

If you'd like to see how to do fuzzing in ``moccasin``, head over to either:

- `Stateless Fuzzing <how-tos/stateless_fuzzing.rst>`_
- `Stateful Fuzzing <how-tos/stateful_fuzzing.rst>`_

What is fuzzing?
================

Fuzzing is a software testing technique that involves providing invalid, unexpected, or random data as inputs to a computer program. The program is then monitored for exceptions such as crashes, or failing built-in code assertions or for finding potential memory leaks. Typically, fuzzers are used to test programs that take structured inputs.

In the smart contract world, fuzzing is one of the best techniques for finding bugs in a codebase, and writing fantastic fuzz tests is one of the best ways to find bugs programatically. 

Often times, we use this "random data" to test to see if our "invariants" are broken.

What are invariants?
====================

Invariants are properties of a program or system that must always remain true. "Fuzzing" or "Fuzz testing" is one of the most popular ways to test for invariants. 

For example:
- For an ERC20 token, the sum of user balances MUST always be less than or equal to the total supply. 
- In the `Aave <https://aave.com/>`_ protocol, it MUST always have more value in collateral than value in loans. 

All systems usually have at least one kind of invariant. Even ERC20/ERC721 tokens have invariants. Some examples are documented in the `Trail of Bits Properties repo. <https://github.com/crytic/properties>`_

With this in mind, if we understand the core invariant of a system, we can write tests to test specifically for that invariant. 

Invariant testing vs Fuzz testing 
=================================

So much so, that often the names are used interchangeably. You'll heard many of these terms:

- Property-based testing
- Invariant testing
- Fuzzing 
- Fuzz testing 
- Stateful testing 
- Hypothesis testing 

And while these are actually all not the same thing, often people are colloquially referring to the same thing.

Stateless Fuzzing
=================

Stateless fuzzing (often known as just "fuzzing") is when you provide random data to a function to get some invariant or property to break. 

It is "stateless" because after every fuzz run, it resets the state, or it starts over. 

Written Example
---------------

You can think of it like testing what methods pop a balloon. 
1. Fuzz run 1:

   1. Get a new balloon

      1. Do 1 thing to try to pop it (ie: punch it, kick it, drop it)
      2. Record whether or not it is popped

2. Fuzz run 2:

   1. Get a new balloon

      1. Do 1 thing to try to pop it (ie: punch it, kick it, drop it)
      2. Record whether or not it is popped

3. *Repeat...* 

Pros & Cons of stateless fuzzing
--------------------------------

Pros:
- Fast to write
- Fast to test

Cons:
- It's stateless, so if a property is broken by calling different functions, it won't find the issue 
- You can never be 100% sure it works, as it's random input

Stateful Fuzzing
================

Stateful fuzzing is when you provide random data to your system, and for each fuzz run your system starts from the resulting state of the previous input data.

Or more simply, you keep doing random stuff to *the same* contract.

Written Example
---------------

You can think of it like testing what methods pop a balloon. 
1. Fuzz run 1:

   1. Get a new balloon

      1. Do 1 thing to try to pop it (ie: punch it, kick it, drop it)
      2. Record whether or not it is popped

   2. If not popped

      1. Try a different thing to pop it (ie: punch it, kick it, drop it)
      2. Record whether or not it is popped

   3. If not popped... *repeat for a certain number of times*

2. Fuzz run 2:

   1. Get a new balloon

      1. Do 1 thing to try to pop it (ie: punch it, kick it, drop it)
      2. Record whether or not it is popped

   2. If not popped

      1. Try a different thing to pop it (ie: punch it, kick it, drop it)
      2. Record whether or not it is popped

   3. If not popped... *repeat for a certain number of times*

3. *Repeat*

Pros & Cons of stateful fuzzing
-------------------------------

Pros:
- Fast to write (not as fast as stateless fuzzing)
- Can find bugs that are from calling functions in a specific order.

Cons:
- You can run into "path explosion" where there are too many possible paths, and the fuzzer finds nothing 
- You can never be 100% sure it works, as it's random input


Where to learn more 
===================

You can learn more about fuzzing from the video here:

.. raw:: html

    <iframe width="560" 
            height="315" 
            src="https://www.youtube.com/embed/juyY-CTolac" 
            title="Fuzzing & Invariants" 
            frameborder="0" 
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
            allowfullscreen>
    </iframe>

And then, learn how to do stateless and stateful fuzz tests in ``moccasin`` from these guides.


- `Stateless Fuzzing <how-tos/stateless_fuzzing.rst>`_
- `Stateful Fuzzing <how-tos/stateful_fuzzing.rst>`_
