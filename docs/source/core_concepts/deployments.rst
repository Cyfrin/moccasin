Deployments
###########

In smart contract development, users often want to interact with contracts they've recently deployed, and keep track of them, so ``moccasin`` comes with a built-in `sqlite3 <https://docs.python.org/3/library/sqlite3.html>`_ database.

Any time you deploy a smart contract, so long as you have your ``save_to_db`` flag set to ``true`` in your `config </api_reference/config_reference>`, ``moccasin`` will automatically save your deployments to the database. Here is an example ``moccasin.toml`` file:

.. code-block:: toml

    [networks.pyevm]
    save_to_db = false # Local and forked networks default to false

    [networks.anvil]
    save_to_db = true # Any other network default to true
    db_path = ".deployments.db" 

Getting a deployment by contract name 
=====================================

You can then, get your latest deployment with any of the following options:

.. code-block:: python 

    from moccasin.config import get_config
    from boa.contracts.abi.abi_contract import ABIContract
    # from boa.deployments import Deployment


    def moccasin_main():
        config = get_config()
        active_network = config.get_active_network()

        # Get the latest counter of the Counter contract
        counter_contract: ABIContract = active_network.get_latest_contract_unchecked("Counter")

This will get you a ``counter_contract`` object that you can interact with. It will look in the database and return the most recently deployed contract on the network that your script is active on. It'll assign the ``ABI`` of your contract when you deployed it to the bytecode at that address. 

There are a number of functions we can call to get either a ``ABIContract`` or ``Deployment`` object. 

- ``get_deployments_unchecked``: This will return all deployments for a given contract name, without checking :ref:`checking integrity <checking_integrity>`.

- ``get_deployments_checked``: This will return all deployments for a given contract name, checking :ref:`checking integrity <checking_integrity>`.

- ``get_latest_deployment_checked``: This will return the latest deployment for a given contract name, checking :ref:`checking integrity <checking_integrity>`.

- ``get_latest_deployment_unchecked``: This will return the latest deployment for a given contract name, without checking :ref:`checking integrity <checking_integrity>`.

- ``get_latest_contract_checked``: This will return the latest contract for a given contract name, checking :ref:`checking integrity <checking_integrity>`. It will convert the ``Deployment`` object to an ``ABIContract``.

- ``get_latest_contract_unchecked``: This will return the latest contract for a given contract name, without checking :ref:`checking integrity <checking_integrity>`. It will convert the ``Deployment`` object to an ``ABIContract``.

- ``get_or_deploy_named_contract``/ ``manifest_named``: This "magical" function will either check the database for a contract, deploy it, check your :doc:`named contracts </core_concepts/named_contracts>`, and a few other places, and if it doesn't find a contract, it will deploy the contract for you. :doc:`You can read more about it here. </core_concepts/named_contracts/manifest_named>`

.. _checking_integrity:

Checked vs Unchecked 
====================

When developing, you'll often make changes to your smart contracts, and you may want to only interact with a contract that matches your current working contract. For example, I could have this code in a file called ``Counter.vy``:

.. code-block:: python 

    # SPDX-License-Identifier: MIT
    # pragma version 0.4.0
    number: public(uint256)
    @external
    def set_number(new_number: uint256):
        self.number = new_number


    @external
    def increment():
        self.number += 1

And deploy it as ``contract A``, then, change it:

.. code-block:: python 

    # SPDX-License-Identifier: MIT
    # pragma version 0.4.0
    number: public(uint256)
    @external
    def set_number(new_number: uint256):
        self.number = new_number

And deploy it as ``contract B``. 

Now, when I call ``get_deployments_checked`` on ``Counter``, it will only return 1 contract, ``contract B`` since that matches the contract that is in my current ``Counter.vy`` file. 

But, if I call ``get_deployments_unchecked`` on ``Counter``, it will return both ``contract A`` and ``contract B``! Since that will only return deployments based on the ``contract_name`` (filename). The way this works, is that under the hood, ``moccasin`` does an integrity check by calling ``has_matching_integrity`` on the ``Network`` class, which compares a hash of each of the contract bytecodes to each other. 