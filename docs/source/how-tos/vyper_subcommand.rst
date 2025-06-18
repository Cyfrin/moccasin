Using the Vyper Subcommand
##########################

Moccasin provides a ``vyper`` subcommand that allows you to run Vyper compiler commands directly through the moccasin CLI. This gives you access to all Vyper functionality while maintaining your moccasin project context.

1. Basic usage
==============

The ``vyper`` subcommand acts as a pass-through to the Vyper compiler:

.. code-block:: bash

    mox vyper [vyper-options] [vyper-arguments]

This allows you to use any Vyper command that you would normally run with the ``vyper`` CLI.

2. Common Vyper commands
========================

Here are some common Vyper commands you can run through moccasin:

**Compile a single contract:**

.. code-block:: bash

    mox vyper contracts/MyContract.vy

**Check Vyper version:**

.. code-block:: bash

    mox vyper --version

**Get help for Vyper options:**

.. code-block:: bash

    mox vyper --help

**Compile with specific output format:**

.. code-block:: bash

    mox vyper -f abi contracts/MyContract.vy

3. Advanced usage examples
==========================

**Generate ABI and bytecode:**

.. code-block:: bash

    mox vyper -f abi,bytecode contracts/MyContract.vy

**Compile with optimization:**

.. code-block:: bash

    mox vyper --optimize codesize contracts/MyContract.vy

**Show compilation statistics:**

.. code-block:: bash

    mox vyper -f opcodes_runtime contracts/MyContract.vy

4. Integration with moccasin projects
=====================================

When using the ``vyper`` subcommand in a moccasin project:

- It automatically uses your project's Vyper configuration
- It respects your project's dependency management
- Contract paths are resolved relative to your project structure

Example project structure:

.. code-block:: text

    my_project/
    ├── moccasin.toml
    ├── contracts/
    │   ├── Token.vy
    │   └── interfaces/
    │       └── IERC20.vy
    └── scripts/
        └── deploy.py

**Compile contracts from project root:**

.. code-block:: bash

    mox vyper contracts/Token.vy

5. Error handling and debugging
===============================

The ``vyper`` subcommand will forward all Vyper compiler errors and warnings:

.. code-block:: bash

    mox vyper contracts/BuggyContract.vy

Any compilation errors will be displayed with full context, making debugging easier while staying within the moccasin environment.