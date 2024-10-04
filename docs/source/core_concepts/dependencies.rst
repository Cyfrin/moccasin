Dependencies 
############

For working with smart contracts, ``moccasin`` allows for working with either:

- :ref:`Installing from GitHub repositories <installing_github_dependencies>`

- :ref:`Installing Python PyPI packages <installing_pip_dependencies>` (these are your "normal" pip packages)

Importantly, the packages/dependencies that you install are *smart contract dependencies only*. Meaning that they are dependencies for your vyper contracts, not for your python scripts.

To see working with python dependencies, go to :doc:`/core_concepts/dependencies/virtual_environments`.


.. _installing_github_dependencies: 

Installing GitHub Dependencies 
==============================

To install a package from GitHub, you can run the following:

.. code-block:: bash

    mox install ORG/REPO[@VERSION]

For example:

.. code-block:: bash

    # Without a version
    mox install pcaversaccio/snekmate
    # With a version
    mox install pcaversaccio/snekmate@0.1.0

This will create an entry in your ``moccasin.toml`` file that looks like this:

.. code-block:: toml

    [project]
    dependencies = [
        "pcaversaccio/snekmate@0.1.0",
    ]

Which follows the same syntax that `pip` and `uv` to do installs from GitHub repositories. This will also download the GitHub repository into your `lib` folder.

You can then use these packages in your vyper contracts, for example in an miniaml ERC20 vyper contract:

.. code-block:: python

    from pcaversaccio.snekmate.src.snekmate.auth import ownable as ow
    initializes: ow

    from pcaversaccio.snekmate.src.snekmate.tokens import erc20
    initializes: erc20[ownable := ow]
    exports: erc20.__interface__

    @deploy
    @payable
    def __init__():
        erc20.__init__("my_token", "MT", 18, "my_token_dapp", "0x02")
        ow.__init__()

``moccasin`` is smart enough to know that the `lib/github` and `lib/pypi` folders are part of the search path, but you can also explicitly add your dependencies.

.. code-block:: python

    # This is the "true" search path
    from lib.github.pcaversaccio.snekmate.src.snekmate.auth import ownable as ow
    initializes: ow

    from lib.github.pcaversaccio.snekmate.src.snekmate.tokens import erc20
    initializes: erc20[ownable := ow]
    exports: erc20.__interface__

    @deploy
    @payable
    def __init__():
        erc20.__init__("my_token", "MT", 18, "my_token_dapp", "0x02")
        ow.__init__()

.. _installing_pip_dependencies: 


Installing uv/pip/PyPI Dependencies 
===================================

Moccasin let's you directly install and work with PyPI packages as you would any other python package. PyPi dependencies in moccasin are by default powered by the `uv <https://docs.astral.sh/uv/>`_ tool under the hood. It comes built-in with ``moccasin``.  

To install a package from PyPI, you can run the following:

.. code-block:: bash

    mox install PACKAGE

For example:

.. code-block:: bash

    mox install snekmate

.. note::

    Snekmate is both a `pypi <https://pypi.org/project/snekmate/>`_ and a GitHub package.

This will create an entry in your ``moccasin.toml`` file that looks like this:

.. code-block:: toml

    [project]
    dependencies = [
        "snekmate==0.1.0",
    ]

You can then use these packages in your vyper contracts, for example in an miniaml ERC20 vyper contract:

.. code-block:: python

    # Vyper will directly inject the package into your contract
    from snekmate.auth import ownable as ow
    initializes: ow

    from snekmate.tokens import erc20
    initializes: erc20[ownable := ow]
    exports: erc20.__interface__

    @deploy
    @payable
    def __init__():
        erc20.__init__("my_token", "MT", 18, "my_token_dapp", "0x02")
        ow.__init__()

.. toctree::
    :maxdepth: 3

    Working with python dependencies <dependencies/virtual_environments.rst>
    Removing dependencies (purge) <dependencies/purging.rst>
    