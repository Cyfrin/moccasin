Configurating Keys 
##################

The preferred method for working with keys, is encrypting them with the :doc:`mox wallet </core_concepts/wallet>` command. 

.. code-block:: toml 

    [networks.zksync]
    default_account_name = "anvil1"

Setting a ``default_account_name`` will make it so that when you run a deploy script, it will automatically attempt to use the keystore file imported as ``anvil1`` (in this example). It will additionally prompt you for a password to decrypt your keystore file for the duration of the script.

You can also pass an ``--unsafe-password-file xxx`` flag or in your ``moccasin.toml`` with the location of a file that holds your password. It uses the ``unsafe`` prefix to alert you that you might not want to make the file's location public!