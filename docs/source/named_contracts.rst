Named Contracts  
###############

One of the major differentiators between moccasin and other smart contract development tools is more flexible and powerful scripting. One of the such cabailities is built in :doc:`fixtures <fixtures>` and :doc:`named contracts <named_contracts>`.

**Named contracts allow you to define deployment scripts, addresses by chain, fixtures settings for testing, and more.**

Named Contract Example 
======================

Let's look at a minimal ``moccasin.toml`` with a ETH mainnet network fork with a named contract:

.. code-block:: toml

    [project]
    src = "contracts"

    [networks.mainnet-fork]
    url = "https://ethereum-rpc.publicnode.com"
    chain_id = 1 
    fork = true

    [networks.mainnet.contracts]
    usdc = { address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"}

The `NamedContract` in this case, is `usdc`. And it's this named contract that we can access our scripts!

.. code-block:: toml 

