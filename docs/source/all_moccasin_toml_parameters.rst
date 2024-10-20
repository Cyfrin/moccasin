All moccasin toml parameters
============================

TOML Formatting
---------------

In TOML you can think of each section as a giant JSON object. Each of these are essentially identical:

+----------------------------------+----------------------------------+----------------------------------+
| TOML (Expanded)                  | TOML (Compact)                   | JSON                             |
+==================================+==================================+==================================+
| .. code-block:: toml             | .. code-block:: bash             | .. code-block:: json             |
|                                  |                                  |                                  |
|    [project]                     |    [project]                     |    {                             |
|    src = "contracts"             |    src = "contracts"             |      "project": {                |
|                                  |    networks = {                  |        "src": "contracts",       |
|    [project.networks.sepolia]    |      sepolia = {                 |        "networks": {             |
|    url = "https://..."           |        url = "https://...",      |          "sepolia": {            |
|    chain_id = 11155111           |        chain_id = 11155111       |            "url": "https://...", |
|                                  |      },                          |            "chain_id": 11155111  |
|    [project.networks.zksync]     |      zksync = {                  |          },                      |
|    url = "https://..."           |        url = "https://...",      |          "zksync": {             |
|    chain_id = 324                |        chain_id = 324            |            "url": "https://...", |
|                                  |      }                           |            "chain_id": 324       |
|                                  |    }                             |          }                       |
|                                  |                                  |        }                         |
|                                  |                                  |      }                           |
|                                  |                                  |    }                             |
+----------------------------------+----------------------------------+----------------------------------+



All possible options
--------------------

.. code-block:: toml

    # Changes the names and locations of specific directories in your project
    [project]
    src = "contracts"
    out = "build"
    script = "scripts"
    lib = "dependencies"
    # You can have pip-style dependencies and also github-style dependencies
    # These are going to be dependencies for your vyper contracts
    dependencies = ["snekmate==0.1.0", "pcaversaccio/snekmate@0.1.0"]
    save_abi_path = "abis" # location to save ABIs from the explorer
    cov_config = ".coveragerc" # coverage configuration file
    dot_env = ".env"  # environment variables file
    default_network = "pyevm" # default network to use. `pyevm` is the local network. "eravm" is the local ZKSync network
    db_path = ".deployments.db" # path to the deployments database

    [networks.pyevm]
    # The basic EVM local network
    # cannot set URL, chain_id, is_fork, is_zksync, prompt_live, explorer_uri, explorer_api_key
    default_account_name = "anvil"

    [networks.eravm]
    # The special ZKSync Era local network
    # cannot set URL, chain_id, is_fork, is_zksync, prompt_live, explorer_uri, explorer_api_key
    default_account_name = "anvil"

    [networks.contracts]
    # Default named contract parameters
    usdc = {"address" = "0x5fbdb2315678afecb367f032d93f642f64180aa3"}

    # Add network settings to easily interact with networks
    [networks.sepolia]
    url = "https://ethereum-sepolia-rpc.publicnode.com"
    chain_id = 11155111
    is_fork = false
    is_zksync = false
    # This is the name of the account that will be unlocked when running on this network
    default_account_name = "anvil"
    # If you don't provide a password or private key, moccasin will prompt you to unlock it 
    # If you do, it will unlock it automatically
    # But be careful about storing passwords and private keys! NEVER store them in plain text
    unsafe_password_file = "/home/user/.moccasin/password"  # Replace with actual path
    explorer_uri = "https://api.etherscan.io/api" # path for the supported explorer 
    explorer_api_key = "your_api_key" # api key for the supported explorer, overrides the main one 
    explorer_type = "blockscout" # If the explorer URL has "blockscout" or "etherscan" in the name, you don't need this
    prompt_live = true # A flag that will prompt you before sending a transaction, it defaults to true for "non-testing" networks 
    save_to_db = true # A flag that will save the deployment to the database, it defaults to true for "non-testing" networks (not pyevm, eravm, or a fork network)
    live_or_staging = true # A flag that will determine if the network is live or staging for the `@pytest.mark.staging` decorator, it defaults to true for non-local, non-forked networks

    [networks.sepolia.contracts]
    # You can override the default named contract parameters
    usdc = {"address" = "0x5fbdb2315678afecb367f032d93f642f64180aa3", abi = "ERC20.vy", force_deploy = false, deployer_script = "script/deploy.py"}

    # You can also format a contract like this, for example, this one is "dai"
    [networks.sepolia.contracts.dai]
    address = "0x6b175474e89094c44da98b954eedeac495271d0f"
    abi = "ERC20.vy"
    force_deploy = false

    [networks.sepolia.extra_data]
    my_data = "hi"

    # Put whatever else you want in here
    [extra_data]
    hi = "hello"

Environment Variables 
---------------------

Additionally, there are a few environment variables that ``moccasin`` will look for, but it's also ok if they are not set. It's important to note, that the `.env` file you set in the config will be ignored for these values. 

.. code-block:: bash 

    MOCCASIN_DEFAULT_FOLDER = "~/.moccasin" # path to the moccasin folder
    MOCCASIN_KEYSTORE_PATH = "~/.moccasin/keystore" # path to the keystore