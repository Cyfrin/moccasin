Dependencies 
############

Dependencies in gaboon are powered by the `uv <https://docs.astral.sh/uv/>`_ tool. Gaboon allows for working with either:
- `GitHub repositories <https://github.com/>`_ 
- `Python PyPI packages <https://pypi.org/>`_ (these are your "normal" pip packages)

Installing GitHub Dependencies 
==============================

To install a package from GitHub, you can run the following:

.. code-block:: bash

    gab install <ORG>/<REPO>

For example:

.. code-block:: bash

    gab install pcaversaccio/snekmate

This will create an entry in your `gaboon.toml` file that looks like this:

.. code-block:: toml

    dependencies = [
        "snekmate @ git+https://github.com/pcaversaccio/snekmate",
    ]

Which follows the same syntax that `pip` and `uv` to do installs from GitHub repositories. This will also download the GitHub repository into your `lib` folder.

You can then use these packages in your vyper contracts, for example in an miniaml ERC20 vyper contract:

.. code-block:: python

    from lib.snekmate.auth import ownable as ow
    initializes: ow

    from lib.snekmate.tokens import erc20
    initializes: erc20[ownable := ow]
    exports: erc20.__interface__

    @deploy
    @payable
    def __init__():
        erc20.__init__("my_token", "MT", 18, "my_token_dapp", "0x02")
        ow.__init__()

Installing PyPI Dependencies 
==============================

You can also directly install and work with PyPI packages as you would any other python package. To install a package from PyPI, you can run the following:

.. code-block:: bash

    gab install <PACKAGE>

For example:

.. code-block:: bash

    gab install snekmate

.. note::

Snekmate is both a `pypi <https://pypi.org/project/snekmate/>`_ and a GitHub package.

This will create an entry in your `gaboon.toml` file that looks like this:

.. code-block:: toml

    dependencies = [
        "snekmate",
    ]
