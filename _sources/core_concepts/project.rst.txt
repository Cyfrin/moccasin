Project Layout 
##############

A typical moccasin project is structured as follows:

.. code-block:: bash

    .
    ├── README.md
    ├── moccasin.toml
    ├── script/
    ├── src/
    ├── tests/
    └── out/

Where:

- ``README.md`` is a markdown file that you can use to describe your project.
- ``moccasin.toml`` is a configuration file that `moccasin` uses to manage the project.
- ``script`` is a directory that contains python scripts that you can use to deploy your project.
- ``src``` is a directory that contains your vyper smart contracts.
- ``tests`` is a directory that contains your tests.
- ``out``` is an optional directory that contains the compiled contracts. In moccasin and titanoboa, contracts are compiled on the fly!

Changing your layout 
====================

If you wanted to adjust your contracts location, for example, have your smart contracts folder be named ``contracts`` instead of ``src``, you'd update your ``moccasin.toml`` file to reflect this change:

.. code-block:: toml

    [project]
    src = "contracts"


Vyper Compiler Options 
======================

By default, ``moccasin`` discourages passing compiler options in the ``moccasin.toml`` file or CLI. Instead, if you wish to use `vyper <https://docs.vyperlang.org/en/stable/>`_ CLI commands, you'll just put them right in the ``pragma`` of the contract:

.. code-block:: python

    # pragma version 0.4.0
    # pragma enable-decimals

    some_value: public(decimal)