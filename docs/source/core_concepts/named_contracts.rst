Named Contracts  
###################

One of the major differentiators between moccasin and other smart contract development tools is more flexible and powerful scripting. One of the such cabailities is built in :doc:`fixtures </core_concepts/testing/fixtures>` and :doc:`named contracts </core_concepts/named_contracts>`.

**Named contracts allow you to define deployment scripts, addresses by chain, fixtures settings for testing, and more.**

Named Contract Example - Minimal Example
========================================

Let's look at a minimal ``moccasin.toml`` with a ETH mainnet network fork with a named contract:

.. code-block:: toml

    [project]
    src = "contracts"

    [networks.mainnet-fork]
    url = "https://ethereum-rpc.publicnode.com"
    chain_id = 1 
    fork = true

    # Look here! We have a named contract named "usdc"
    [networks.mainnet-fork.contracts]
    usdc = { address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"}

The `NamedContract` in this case, is `usdc`. And it's this named contract that we can access our scripts!

.. code-block:: python 

    from moccasin.config import get_config

    def print_contract_address():
        active_network = get_config().get_active_network()
        named_contract = active_network.get_named_contract("usdc")
        print(named_contract.address)

    def moccasin_main():
        print_contract_address()

We could run this script, and it would, print out the address from our config. 

.. code-block:: bash 

    mox run print_contract_address --network mainnet-fork

    0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48


.. _manifest_intro:

Named Contract Example - Interacting with the contract 
======================================================

Now, just getting the address is pretty boring, typically you want to interact with the contract. To do so, we have a number of parameters you can set in the config to get the contract ABI (Application Binary Interface).

.. note::

    You can learn more about what an ABI is from `Cyfrin Updraft <https://updraft.cyfrin.io/courses/solidity/storage-factory/interacting-with-smart-contracts-abi?lesson_format=video>`_ or the `Cyfrin Blog <https://www.cyfrin.io/blog/what-is-a-smart-contract-abi-and-how-to-get-it>`_.

There are a number of flags we can set for our ``NamedContract``:

.. tabs:: 
    
    .. code-tab:: toml true-toml

        [networks.mainnet-fork.contracts.usdc]
        address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
        abi = "ERC20.vy"
        abi_from_explorer = true
        deployment_script = "script/deploy_erc20.py"
        force_deploy = false
    
    .. code-tab:: bash ugly-toml
        
        # Did you know that this format will work the same?
        # It's technically the "uglier" version toml 
        [networks.mainnet-fork.contracts]
        usdc = {
            address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
            abi = "ERC20.vy"
            abi_from_explorer = true
            deployment_script = "script/deploy_erc20.py"
            force_deploy = false
        }

Let's break these down:

- ``address``: The address of the contract on the network.
- ``abi```: The ABI source of the contract. This is can be any of the following:
    - ``.json`` file path to an ABI file
    - ``.vy`` file path to a Vyper contract
    - *Coming soon* ``.vyi`` file path to a Vyper interface
    - A "raw" ABI string
- ``abi_from_explorer``: If you want to get the ABI from an explorer. This is useful if you don't have the ABI and you want to get it from a public source. You'll need to set a ``explorer_api_key`` in your ``moccasin.toml``, or an ``EXPLORER_API_KEY`` environment variable.
- ``deployment_script``: The path to the :doc:`deployment script </core_concepts/scripting/deploy>` for this named contract, this will be a shorthand for deploying in the future. 
- ``force_deploy```: If you want to force deploy the contract when :ref:`manifesting <manifesting>` the contract.

As we know, to interact with a contract, one of the most important things is the ABI. For us to interact with any named contract, we give it an ABI, and we can start interacting with that named contract using the ``manifest_named`` function. 

.. code-block:: python 

    from moccasin.config import get_config

    def print_contract_address():
        active_network = get_config().get_active_network()
        usdc: VyperContract = active_network.manifest_named("usdc")
        decimals = usdc.decimals()
        print(decimals)

    def moccasin_main():
        print_contract_address()

And running this on ``mainnet-fork`` will get the resulting output:

.. code-block:: bash

    # Run this 
    mox run print_contract_address --network mainnet-fork

    # Output
    6 # USDC has 6 decimals because it is weird

The key here, was the ``mainifest_contract``, which does a lot of things under the hood, including:

- Deploys a contract if one doesn't exist
- Allows us to get fixtures for testing 
- Returns the named contract at it's address if it's on a chain we recognize 
- Sets up local testing environments for us to test our contracts

And more! Let's read more about the power of ``NamedContract``\s and how they can help you in your development process.


.. toctree::
    :maxdepth: 2

    Manifest Named Contract <named_contracts/manifest_named.rst>
    