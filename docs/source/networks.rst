Networks 
========

Networks in `gaboon` are identified in your `gaboon.toml`. The complete list of options you can set for your network can be identified in the example here:

.. code-block:: toml

    [networks.sepolia]
    url = "https://ethereum-sepolia-rpc.publicnode.com"
    chain_id = 11155111
    is_fork = false
    is_zksync = false
    default_account_name = "anvil"
    unsafe_password_file = "~/.gaboon/password"
    extra_data = { "my_key" = "{$ETHERSCAN_API_KEY}" }

Let's walk through what each of these options mean. 

- `url`: The URL of the network you are connecting to.
- `chain_id`: The chain ID of the network you are connecting to.
- `is_fork`: If you are forking a network, set this to `true`.
- `is_zksync`: If you are connecting to a zkSync network, set this to `true`.
- `default_account_name`: The default account name to use when deploying contracts. This will be the name of your account you created with your :doc:`wallet <wallet>`_ command.
- `unsafe_password_file`: The location of the password file for your account. This is a file that contains the password for your account. BE SURE TO NEVER PUSH THIS PASSWORD TO GITHUB IF YOU USE THIS. 
- extra-data: This is a dictionary of extra data you can use in your contracts. 

You'll notice there is no `private-key`. We highly discourage having private keys in plain text. 

When working with a network from the command line, for example to :doc:`run a script <script>`_ you can pass the `--network` flag via the command line, and it will load the data from the network in your `gaboon.toml`.

For example, if you wanted to run a script on the `sepolia` network, you would run:

.. code-block:: bash

    gaboon run my_script --network sepolia

Since in our example we passed both a `default_account_name` and a `unsafe_password_file`, `gaboon` will automatically unlock the account for you. If you don't pass a `default_account_name` or a `unsafe_password_file`, `gaboon` will error saying it cannot find your account.