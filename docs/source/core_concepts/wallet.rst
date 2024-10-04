Wallet
######

By default, you don't want to ever expose your private key in your scripts. You can use the `wallet` commands to manage your private keys and accounts.

.. code-block:: bash

    mox wallet --help

    usage: Moccasin CLI wallet [-h] [-d] [-q] {list,ls,generate,g,new,import,i,add,view,decrypt,dk,delete,d} ...

    Wallet management utilities.

    positional arguments:
    {list,ls,generate,g,new,import,i,add,view,decrypt,dk,delete,d}
        list (ls)           List all the accounts in the keystore default directory
        generate (g, new)   Create a new account with a random private key
        import (i, add)     Import a private key into an encrypted keystore
        view                View the JSON of a keystore file
        decrypt (dk)        Decrypt a keystore file to get the private key
        delete (d)          Delete a keystore file

    options:
    -h, --help            show this help message and exit
    -d, --debug           Run in debug mode
    -q, --quiet           Suppress all output except errors

Encrypting a private key
========================

You can encrypt a private key using the `wallet import ACCOUNT_NAME` command. This will create a keystore file in the default keystore directory. It will prompt you to enter your private key and password.

.. code-block:: bash

    $ mox wallet import my_account

    Running wallet command...
    Importing private key...
    Enter your private key:  ...

Once you have an account, you can view it with the `wallet list` command.

.. code-block:: bash

    $ mox wallet list

    Running wallet command...
    Found 1 accounts:
    my_account 

This will encrypt your key and store it at `~/.moccasin/keystore/my_account.json`. You can view the contents of the keystore file with the `wallet inspect` command.

.. code-block:: bash 

    $ mox wallet inspect my_account
    Running wallet command...
    Keystore JSON for account my_account:
    {
        "address": "f39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        "crypto": {
            "cipher": "aes-128-ctr",
            "cipherparams": {
                "iv": "e6966dcf6d5384f050052f71ed7bfc02"
            },
            "ciphertext": "decc1fbd482a171578028bfb2563362b9f4857765d6247900bde22e0cd6c2c13",
            "kdf": "scrypt",
            "kdfparams": {
                "dklen": 32,
                "n": 262144,
                "r": 8,
                "p": 1,
                "salt": "71326ecf78c3a2f2087366e4516d44f1"
            },
            "mac": "62dbc22cce0e270a71a5ac1a8c57b04eafa215839abcbdb9f349d63b6b9e5e9f"
        },
        "id": "ea0a89c0-04ea-4120-b6a4-b55fbb0baade",
        "version": 3
    }

You can then use these in scripts!

.. code-block:: bash 

    mox run deploy --account my_account 

And it will ask you for the password to decrypt your private key.



.. toctree::
    :maxdepth: 2

    Private Keys <wallet/private_key.rst>
    Accounts in mocasin.toml <wallet/config_keys.rst>
    