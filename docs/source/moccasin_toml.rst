moccasin.toml
##############

The `moccasin.toml` file created is our configuration file. In this file we can have:

- project and layout settings 

- network settings 

- dependencies settings

- extra data

A `moccasin.toml` file can look like this:

.. code-block:: toml

    [project]
    src = "contracts"

    [networks.sepolia]
    url = "https://ethereum-sepolia-rpc.publicnode.com"
    chain_id = 11155111

    [extra_data]
    my_key = "{$ETHERSCAN_API_KEY}"


You can learn more about each of the sections of the `moccasin.toml` file in their respective documentation.

- `Project <project>`_
- `Network <network>`_
- `Dependencies <dependencies>`_

You can also see a full example of a `moccasin.toml` in the :doc:`all moccasin toml parameters <all_moccasin_toml_parameters>` documentation.

Extra Data 
==========

Extra data is a dictionary of data where you can put whatever you'd like. You can access it from your scripts with:

.. code-block:: python

    from moccasin import config
    print(config.get_config().extra_data["my_key"])