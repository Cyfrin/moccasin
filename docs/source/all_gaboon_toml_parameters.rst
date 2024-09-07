All gaboon toml parameters
===========================

.. code-block:: toml

    # You can have python dependencies and also straight github dependencies
    # These are going to be dependencies for your vyper contracts
    dependencies = ["snekmate==0.1.0", "snekmate @ git+https://github.com/pcaversaccio/snekmate"]

    # Changes the names and locations of specific directories in your project
    [layout]
    src = "contracts"
    out = "build"
    script = "scripts"
    lib = "dependencies"

    # Add network settings to easily interact with networks
    [networks.sepolia]
    url = "https://ethereum-sepolia-rpc.publicnode.com"
    chain_id = 11155111
    is_fork = false
    is_zksync = false
    # This is the name of the account that will be unlocked when running on this network
    default_account_name = "anvil"
    # If you don't provide a password or private key, gaboon will prompt you to unlock it 
    # If you do, it will unlock it automatically
    # But be careful about storing passwords and private keys! NEVER store them in plain text
    unsafe_password_file = "/home/user/.gaboon/password"  # Replace with actual path

    [networks.sepolia.extra_data]
    my_key = "{$ETHERSCAN_API_KEY}"

    # It might be a good idea to place addresses in here!
    [networks.mainnet.extra_data]
    usdc = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

    # Put whatever else you want in here
    [extra_data]
    hi = "hello"