Contract Verification
#####################

The `titanoboa <https://github.com/vyperlang/titanoboa/>`_ tool comes with built in contract verification. To make life easier, we created a wrapper function called ``moccasin_verify`` that you can use to verify contracts.


1. Setup your explorer
=======================

In your ``moccasin.toml`` add your explorer details:

.. code-block:: toml 

    explorer_uri = "https://explorer.sepolia.era.zksync.dev"
    explorer_type = "zksyncexplorer"
    explorer_api_key = "None"

Some networks, like ``sepolia-zksync``, have some of these details defaulted for you. You can check out the :doc:`/explorer_network_defaults` page to see what's available. As of today, the only supported explorers are:

- `Blockscount explorer <https://www.blockscout.com/>`_
- `ZKsync explorer <https://explorer.zksync.io/>`_


2. Add ``moccasin_verify`` to your script
=========================================

In your script, let say, named ``deploy_and_verify.py``, you can run the following code:

.. code-block:: python

    def moccasin_main():
        active_network = get_active_network()
        counter = Counter.deploy()
        print("Counter deployed at", counter.address)
        result = active_network.moccasin_verify(counter)
        result.wait_for_verification()
        print("Counter verified")


3. Run your script
==================

.. code-block:: bash

    mox run deploy_and_verify.py --network my_network

That's it! 
