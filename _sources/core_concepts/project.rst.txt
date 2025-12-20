Project Layout 
##############

A typical moccasin project is structured as follows:

.. code-block:: bash

    .
    ├── README.md
    ├── lib/
    ├── moccasin.toml
    ├── script/
    ├── src/
    ├── tests/
    └── out/

Where:

- ``README.md`` is a markdown file that you can use to describe your project.
- ``lib/`` is a directory that contains :doc:`moccasin depedencies <dependencies>` that you can use inside your contracts.
- ``moccasin.toml`` is a configuration file that ``moccasin`` uses to manage the project.
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

You can also change the location of your scripts, compiler output, and moccasin libraries by updating the ``moccasin.toml`` file.

See :doc:`moccasin toml parameters </all_moccasin_toml_parameters>` doc for a full list of options you can set in your ``moccasin.toml`` file.


Vyper Compiler Options 
======================

By default, ``moccasin`` discourages passing compiler options in the ``moccasin.toml`` file or CLI. Instead, if you wish to use `vyper <https://docs.vyperlang.org/en/stable/>`_ CLI commands, you'll just put them right in the ``pragma`` of the contract:

.. code-block:: python

    # pragma version >=0.4.1
    # pragma enable-decimals

    some_value: public(decimal)

See other `vyper compiler options <https://docs.vyperlang.org/en/stable/compiling-a-contract.html#enabling-experimental-code-generation>`_ for more information.