Getting started with ZKsync 
###########################

Installation
============

To get started with ZKsync on moccasin, you'll need the following:

- `era_test_node <https://github.com/matter-labs/era-test-node>`_

  - You'll know you did it right if you can run ``era_test_node --version`` and you see a response like ``era_test_node 0.1.0 (a178051e8 2024-09-07)``

- `era-compiler-vyper <https://github.com/matter-labs/era-compiler-vyper>`_

  - You'll know you did it right if you can run ``zkvyper --version`` and you see a response like ``Vyper compiler for ZKync v1.5.4 (LLVM build f9f732c8ebdb88fb8cd4528482a00e4f65bcb8b7)``

Testing 
=======

To test on a local zksync network, run the following:

.. code-block:: bash

    mox test --network eravm 

And you'll spin up a local zksync network, and run your tests on it! You can then deploy, test, and verify contracts as you would any other network. 

.. note::

    As of today, ``moccasin`` does not support "system contracts" or "simulations", therefore, testing things like native account abstraction are not yet supported. You can "do" them, but they will require custom scaffolding.

Deployment 
==========

To deploy to a zksync network, you have to do a lot of work.

1. Setup your network
=====================

.. code-block:: toml 

    [networks.sepolia-zksync]
    url = "$SEPOLIA_ZKSYNC_RPC_URL"
    is_zksync = true

2. Run your script 

.. code-block:: bash

    mox run deploy.py --network sepolia-zksync

That's it! ``moccasin`` can handle ZKsync networks just like any other network.