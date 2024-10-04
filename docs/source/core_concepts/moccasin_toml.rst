moccasin.toml
##############

.. note:: 

    For an exhaustive list of options for your ``moccasin.toml`` file, see the :doc:`all moccasin toml parameters </all_moccasin_toml_parameters>` documentation.

The ``moccasin.toml`` file created is our configuration file. In this file we can have:

- project and layout settings 

- network settings 

- dependencies settings

- extra data

A ``moccasin.toml`` file can look like this:

.. code-block:: toml

    [project]
    dependencies = ["snekmate==0.1.0"]
    src = "contracts"
    explorer_api_key = "${ETHERSCAN_API_KEY}"
    dot_env = ".env"

    [networks.sepolia]
    url = "https://ethereum-sepolia-rpc.publicnode.com"
    chain_id = 11155111

    [extra_data]
    my_key = "other_data"


You can learn more about each of the sections of the ``moccasin.toml`` file in their respective documentation.

- :doc:`Project <project>`
- :doc:`Networks <networks>`
- :doc:`Dependencies <dependencies>`

You can also see a full example of a ``moccasin.toml`` in the :doc:`all moccasin toml parameters </all_moccasin_toml_parameters>` documentation.

Extra Data 
==========

Extra data is a dictionary of data where you can put whatever you'd like. You can access it from your scripts with:

.. code-block:: python

    from moccasin import config
    print(config.get_config().extra_data["my_key"])

Order Of Operations 
===================

Whenever you run a script, you'll want to remember this order:

1. Script 
2. Command Line 
3. ``moccasin.toml``
4. Defaults 

Whatever you place in your python script, will be the value used, even if your command line has a different value. Similarly, any flag passed to the command line will override any values in your ``moccasin.toml``, which will override any default values moccasin sets.

This allows you to set your config file up, but if you want to make a tweak you don't have to touch your source code, you can just adjust it on the fly!