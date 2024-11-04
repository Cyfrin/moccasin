.. _manifesting:

Manifest Named Contract (``get_or_deploy_named_contract``)
==========================================================

.. note::

    Be sure to at least read :ref:`manifest introduction <manifest_intro>` before continuing here.

An issue that developers run into when creating smart contracts, is knowing how to make their deployment and scripting pipelines portable and flexible. 

- What happens if you change chains that you want to deploy to?
- How can you test to make sure your deploy scripts work exactly the way your tests run?
- If I want to simulate a test with a `forked test <forked-networks.rst>`, will my scripts still work?

This is where the ``manifest_named`` aka ``get_or_deploy_named_contract`` function comes in. Let's say you have a smart contract that has an address as a constructor parameter, because the address is different on different chains. This additionally is very helpful in testing, and ``NamedContract``\s have built-in ``pytest`` :doc:`fixtures </core_concepts/testing/fixtures>`.

Interacting with a contract on multiple networks with one script 
----------------------------------------------------------------

Let's take the following contract:

.. code-block:: python 

    # pragma version 0.4.0
    # SPDX-License-Identifier: MIT
    from interfaces import ERC20

    usdc: public(ERC20)

    @deploy
    def __init__(usdc: address):
        self.usdc = ERC20(usdc)
    
    @external
    def get_usdc_decimals() -> uint256:
        return self.usdc.decimals()

We want to be able to test this contract on:

- A locally running network 
- A forked network 
- A testnet 
- A mainnet 
- Potentially a second mainnet 

In order for us to do this traditionally, we'd have to write a separate script *for every single one of these cases*. For example:

.. code-block:: python 

    if network.name == "locally_running_chain":
        # do something...
    elif network.name == "forked_chain":
        # do something...
    elif network.name == "testnet":
        # do something...
    elif network.name == "mainnet":
        # do something...
    elif network.name == "second_mainnet":
        # do something...

And this is awful! So instead, what we can do, is setup **ALL** of the configuration in our ``moccasin.toml`` file and use the magic ``manifest_named`` function to automatically deploy the contract on the correct network, with the correct parameters. Let's look at the ``moccasin.toml`` file:

.. code-block:: toml 

    # At the top, we can set some default parameters for the `usdc` named contract 
    # Every named contract will use the ERC20.vy contract in the project as it's ABI 
    # If the contract doesn't exist, it'll deploy with the `deploy_feed.py` script (for example, on a locally running network)
    [networks.contracts]
    usdc = { abi = "ERC20", deployer_script = "mock_deployer/deploy_feed.py"}

    # We can then set the parameters for each network
    [networks.mainnet]
    url = "mainnet_url" # Enter your mainnet url here

    [networks.mainnet.contracts]
    usdc = { address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48" }

    [networks.sepolia]
    url = "sepolia_url" # Enter your mainnet url here

    [networks.sepolia.contracts]
    usdc = { address = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238" }

    [networks.arbitrum]
    url = "arbitrum" # Enter your mainnet url here

    [networks.arbitrum.contracts]
    usdc = { address = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831" }

And with this, we only need ONE script that works for all of these! 

.. code-block:: python 

    from moccasin.config import get_config

    def get_decimals():
        active_network = get_config().get_active_network()
        usdc: VyperContract = active_network.manifest_named("usdc")
        decimals = usdc.decimals()
        print(decimals)


    def moccasin_main():
        get_decimals()

Then, we just need to adjust the `--network` flag and everything else will work automatically.

.. code-block:: bash

    # Mainnet
    mox run get_decimals --network mainnet
    # Sepolia
    mox run get_decimals --network sepolia
    # Arbitrum
    mox run get_decimals --network arbitrum

    # These next two are special 

    # Forked
    mox run get_decimals --network mainnet --fork
    # Local (pyevm)
    mox run get_decimals 

The first 3 commands will do as you expect, directly connecting to the URL you set in your ``moccasin.toml`` file. The last two are special:

- The ``--fork`` flag will setup your script to run locally, using your ``mainnet`` url. 
- If you don't specify a network, you'll use the special locally running :doc:`pyevm </core_concepts/networks/pyevm>` network.