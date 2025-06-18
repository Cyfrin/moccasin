Format Vyper Code
#################

Moccasin provides a ``format`` command that allows you to automatically format your Vyper code. This feature requires the ``mamushi`` tool to be installed.

1. Prerequisites
================

Before using the format command, you need to install ``mamushi``. We recommend using ``uv`` for installation:

.. code-block:: bash

    uv tool install mamushi

Alternatively, you can install it with pip:

.. code-block:: bash

    pip install mamushi

2. Basic usage
==============

To format a single Vyper file:

.. code-block:: bash

    mox format contracts/MyContract.vy

To format all Vyper files in your project:

.. code-block:: bash

    mox format contracts/

3. Format specific files
========================

**Format a single contract:**

.. code-block:: bash

    mox format contracts/Token.vy

**Format multiple specific files:**

.. code-block:: bash

    mox format contracts/Token.vy contracts/Vault.vy

**Format all files in a directory:**

.. code-block:: bash

    mox format contracts/

4. Integration with project workflow
====================================

The format command works seamlessly with your moccasin project structure:

.. code-block:: text

    my_project/
    ├── moccasin.toml
    ├── contracts/
    │   ├── Token.vy
    │   ├── Vault.vy
    │   └── interfaces/
    │       └── IERC20.vy
    └── scripts/
        └── deploy.py

**Format all contracts:**

.. code-block:: bash

    mox format contracts/

**Format contracts and interfaces:**

.. code-block:: bash

    mox format contracts/ contracts/interfaces/

5. Formatting standards
=======================

The ``mamushi`` formatter applies consistent styling to your Vyper code, including:

- Consistent indentation
- Proper spacing around operators
- Standardized line breaks
- Uniform comment formatting

6. Before and after example
===========================

**Before formatting:**

.. code-block:: python

    #pragma version ^0.4.0
    
    @external
    def transfer(to:address,amount:uint256)->bool:
        assert to!=empty(address)
        self.balances[msg.sender]-=amount
        self.balances[to]+=amount
        return True

**After formatting:**

.. code-block:: python

    # pragma version ^0.4.0
    
    @external
    def transfer(to: address, amount: uint256) -> bool:
        assert to != empty(address)
        self.balances[msg.sender] -= amount
        self.balances[to] += amount
        return True

7. Integration with development workflow
========================================

Consider integrating the format command into your development workflow:

**Pre-commit formatting:**

.. code-block:: bash

    # Format all contracts before committing
    mox format contracts/ && git add contracts/

**Continuous formatting during development:**

.. code-block:: bash

    # Format and compile in one go
    mox format contracts/ && mox compile