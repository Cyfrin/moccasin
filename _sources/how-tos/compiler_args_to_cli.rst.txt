How to pass vyper compiler args through the CLI 
###############################################

You don't! 

This is a bit of an anti-pattern that ``moccasin`` currently does not support. It is much safe to list your compiler args directly in the Vyper files themselves.

Setting the Enable Decimals Flag
=================================

In ``moccasin``, you **can only** set compiler flags like ``enable-decimals`` directly in your Vyper smart contract using a source code pragma, as compiler arguments are not supported.

Adding the following pragma to a contract enables decimal support:

.. code-block:: python

    # pragma enable-decimals

The ``enable-decimals`` flag **must** be set on the Vyper smart contract itself using this pragma syntax.

Setting the Target EVM Version
===============================

When you compile your contract code, you can specify the target Ethereum Virtual Machine version to compile for, to access or avoid particular features. In ``moccasin``, you **can only** set the EVM version directly in your Vyper smart contract using a source code pragma, as compiler arguments are not supported.

Adding the following pragma to a contract indicates that it should be compiled for the "prague" fork of the EVM:

.. code-block:: python

    # pragma evm-version prague

The EVM version **must** be set on the Vyper smart contract itself using this pragma syntax.

For more information about pragmas, see the `Vyper documentation <https://docs.vyperlang.org/en/latest/structure-of-a-contract.html#pragmas>`_.