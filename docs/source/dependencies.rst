Dependencies 
############


Gaboon allows for working with either:

- :ref:`Installing from GitHub repositories <installing_github_dependencies>`

- :ref:`Installing Python PyPI packages <installing_pip_dependencies>` (these are your "normal" pip packages)


.. _installing_github_dependencies: 

Installing GitHub Dependencies 
==============================

To install a package from GitHub, you can run the following:

.. code-block:: bash

    gab install ORG/REPO[@VERSION]

For example:

.. code-block:: bash

    # Without a version
    gab install pcaversaccio/snekmate
    # With a version
    gab install pcaversaccio/snekmate@0.1.0

This will create an entry in your `gaboon.toml` file that looks like this:

.. code-block:: toml

    [project]
    dependencies = [
        "pcaversaccio/snekmate@0.1.0",
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


.. _installing_pip_dependencies: 


Installing pip/PyPI Dependencies 
================================

Gaboon let's you directly install and work with PyPI packages as you would any other python package. PyPi dependencies in gaboon are by default powered by the `uv <https://docs.astral.sh/uv/>`_ tool. In order to use this, you need to have the `uv` tool installed. However, you can change this setting to `pip` in your `gaboon.tom`.

.. code-block:: toml

    [project]
    installer = "pip" # change/add this setting

As of today, `gaboon` supports:

- `pip`

- `uv`

You can also directly install and work with PyPI packages as you would any other python package. To install a package from PyPI, you can run the following:

.. code-block:: bash

    gab install PACKAGE

For example:

.. code-block:: bash

    gab install snekmate

.. note::

    Snekmate is both a `pypi <https://pypi.org/project/snekmate/>`_ and a GitHub package.

This will create an entry in your `gaboon.toml` file that looks like this:

.. code-block:: toml

    [project]
    dependencies = [
        "snekmate==0.1.0",
    ]
