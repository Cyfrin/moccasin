Staging Markers
###############

Have you ever wanted to run a test on a live network, but don't want any of your other tests to run? Well, with ``moccasin`` you can!

The idea
========

A lot of developers `should` run some sanity checks on a live network, for example if you're working with:

- Oracles 
- Setup tricks
- etc 

Maybe after you deploy your contracts, you want to run a quick test suite to make sure everything is ok, this is where "staging" tests come into play.

How to use staging markers
==========================

.. code-block:: python
    
    @pytest.mark.staging 
    def test_staging_test(counter_contract):
        counter_contract.increment()
        assert counter_contract.number() == 2

    def test_normal_test(counter_contract):
        counter_contract.increment()
        assert counter_contract.number() == 2

The two tests above look the same, except for the ``staging`` marker. If we run our test suite normally:

.. code-block:: bash

    mox test 

Only the ``test_normal_test`` will run. But, let's say we had a network named ``sepolia``, if we run:

.. code-block:: bash

    mox test --network sepolia

Then `only` the ``test_staging_test`` will run! 


How it works 
============

In your ``moccasin.toml`` file, you can assign a ``live_or_staging`` boolean:

.. code-block:: toml 

    [networks.sepolia]
    live_or_staging = true 

If it's set to ``true``, then any test on this network will not run unless it has the ``staging`` marker. 

Defaults
========

- Local networks (``pyevm`` and ``eravm``) have this defaulted to ``false``.
- Forked networks (set by ``--fork`` or ``fork = true`` in your config) have this defaulted to ``false``.
- All other networks have this defaulted to ``true``.

What if I want my staging test to also run on my local networks?
================================================================

To have a staging test also run on local and forked networks, you can do:

.. code-block:: python
    
    @pytest.mark.staging
    @pytest.mark.local # See this!
    def test_staging_test(counter_contract):
        counter_contract.increment()
        assert counter_contract.number() == 2

    def test_normal_test(counter_contract):
        counter_contract.increment()
        assert counter_contract.number() == 2

