Named Contracts  
###############

One of the major differentiators between moccasin and other smart contract development tools is more flexible and powerful scripting. One of the such cabailities is built in :doc:`fixtures <fixtures>` and :doc:`named contracts <named_contracts>`.

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

    from moccasin import config

    def print_contract_address():
        active_network = config.get_config().get_active_network()
        named_contract = active_network.get_named_contract("usdc")
        print(named_contract.address)

    def moccasin_main():
        print_contract_address()

We could run this script, and it would, print out the address from our config. 

.. code-block:: bash 

    mox run print_contract_address --network mainnet-fork


Named Contract Example - Interacting with the contract 
======================================================

Now, just getting the address is pretty boring, typically you want to interact with the contract. To do so, we have a number of parameters you can set in the config to get the contract ABI (Application Binary Interface).

.. note::

    You can learn more about what an ABI is from [Cyfrin Updraft](https://updraft.cyfrin.io/courses/solidity/storage-factory/interacting-with-smart-contracts-abi?lesson_format=video) or the [Cyfrin Blog](https://www.cyfrin.io/blog/what-is-a-smart-contract-abi-and-how-to-get-it).

There are a number of flags we can set for our `NamedContract`:

.. code-block:: toml

    [networks.mainnet-fork.contracts]
    usdc = { 
        address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        # abi = "raw ABI string here...",
        abi_from_file = "src/ERC20.json",
        abi_from_explorer = true
        fixture = false,
        deployment_script = "script/deploy_erc20.py",
        force_deploy = false
    }

Let's break these down:

- `address`: The address of the contract on the network.
- `abi`: The ABI of the contract. This is a raw string of the ABI. (Not recommended)
- `abi_from_file`: The path to the ABI file. This is the recommended way to get the ABI. This can be a:
    - JSON file
    - ``.vy`` file 
    - *Coming soon* A ``.vyi`` file 
- `abi_from_explorer`: If you want to get the ABI from an explorer. This is useful if you don't have the ABI and you want to get it from a public source. You'll need to set a ``explorer_api_key`` in your ``moccasin.toml``, or an ``EXPLORER_API_KEY`` environment variable.
- `fixture`: If you want to use this contract as a :doc:`fixture <fixture>`. 
- `deployment_script`: The path to the :doc:`deployment script <deploy>`` for this named contract, this will be a shorthand for deploying in the future. 
- `force_deploy`: If you want to force deploy the contract whenever you refer to this named contract. 

