Deploy
######

.. code-block:: bash

    mox deploy --help
    usage: Moccasin CLI deploy [-h] [-d] [-q] [--fork [FORK]] [--network NETWORK | --url URL | --prompt-live [PROMPT_LIVE]]
                            [--account ACCOUNT | --private-key PRIVATE_KEY] [--password PASSWORD | --password-file-path PASSWORD_FILE_PATH]
                            contract_name

    Deploys a contract named in the config with a deploy script.

    positional arguments:
    contract_name         Name of contract in your moccasin.toml to deploy.

    options:
    -h, --help            show this help message and exit
    -d, --debug           Run in debug mode
    -q, --quiet           Suppress all output except errors
    --fork [FORK]
    --network NETWORK     Alias of the network (from the moccasin.toml).
    --url URL, --rpc URL  RPC URL to run the script on.
    --prompt-live [PROMPT_LIVE]
                            Prompt the user to make sure they want to run this script.
    --account ACCOUNT     Keystore account you want to use.
    --private-key PRIVATE_KEY
                            Private key you want to use to get an unlocked account.
    --password PASSWORD   Password for the keystore account.
    --password-file-path PASSWORD_FILE_PATH
                            Path to the file containing the password for the keystore account.

The ``deploy`` command is very similar to the :doc:`run </core_concepts/script>` command, except it specifically works with :doc:`NamedContracts </core_concepts/named_contracts>` that have a ``deployer_script`` defined.

In your ``moccasin.toml`` file, like this:

.. code-block:: toml 

    [networks.contracts]
    usdc = {  deployer_script = "script/deploy_usdc.py" }

You can directly deploy that script without using the ``run`` command, and instead:

.. code-block:: bash

    mox deploy usdc 

Which is essentially equivalent to running:

.. code-block:: bash

    mox run script/deploy_usdc.py
