gaboon.toml
##############

The `gaboon.toml` file created is our configuration file. In this file we can have:
- project layout settings 
- network settings 
- dependencies 
- extra data

A `gaboon.toml` file can look like this:

.. code-block:: toml

    [layout]
    src = "contracts"

    [networks.sepolia]
    url = "https://ethereum-sepolia-rpc.publicnode.com"
    chain_id = 11155111

    [extra_data]
    my_key = "{$ETHERSCAN_API_KEY}"


You can learn more about each of the sections of the `gaboon.toml` file in their respective documentation.

- `Layout <layout>`_
- `Network <network>`_
- `Dependencies <dependencies>`_

You can also see a full example of a `gaboon.toml` in the :doc:`all gaboon toml parameters <all_gaboon_toml_parameters>` documentation.

Extra Data 
==========

Extra data is a dictionary of data where you can put whatever you'd like. You can access it from your scripts with:

.. code-block:: python

    from gaboon import config
    print(config.get_config().extra_data["my_key"])