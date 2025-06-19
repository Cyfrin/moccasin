Common Errors
=============

ValueError: <boa.network.NetworkEnv object at 0xXXXXXXXXX>.eoa not defined!
----------------------------------------------------------------------------

This is the most common error you'll encounter, and it means you'll need to add an account to your ``moccasin.toml`` file. You can do this by following the :doc:`wallet <core_concepts/wallet>` guide.

----

FileNotFoundError: [Errno 2] No such file or directory: 'lib'
--------------------------------------------------------------
This error occurs when Moccasin cannot find the `lib` directory in your project, or it is missing ``github`` and/or ``pypi`` directory. 
To fix this, you can create the `lib` directory in your project root:

.. code-block:: bash

    mkdir lib
    mkdir lib/github
    mkdir lib/pypi

Or with recent versions of Moccasin, you can run ``mox install`` to automatically create the `lib` directory and its subdirectories.

----

VersionException: Version specification ``"==x.x.x"`` is not compatible with compiler version
-------------------------------------------------------------------------------------------------------------------

This error usually occurs with VSCode and its `Vyper extension <https://marketplace.visualstudio.com/items?itemName=tintinweb.vscode-vyper>`_.
By default, the extension will use your global Vyper installation, which may not match the version specified in your ``pyproject.toml`` file.
If you have initialized your project with ``mox init --vscode``, you can fix this by changing the following setting in your VSCode ``.vscode/settings.json`` file:

.. code-block:: json

    {
        // ...
        "vyper.command": "vyper -p ./lib/github -p ./lib/pypi"
    }

You can change it like this to get the vyper version from your project's virtual environment:

.. code-block:: json

    {
        // ...
        "vyper.command": "./.venv/bin/vyper -p ./lib/github -p ./lib/pypi"
    }

----

AssertionError: Bytecode length must be a multiple of 32 bytes (ZKsync)
------------------------------------------------------------------------

This error occurs when you try to deploy a contract on ZKsync and it might not be related to the feedback from the compiler.
Usually, it is because ``moccasin`` installed with ``uv tool`` comes with its own dependencies installed by default to the latest version.
Therefore, if you use ``mox`` from the tool, it will try to deploy with its own ``vyper`` depedency. 

To fix this, you need to add ``moccasin`` to your project's virtual environment and install the dependencies there.
You can do this by running the following command in your project directory:

.. code-block:: bash

    uv add moccasin
    uv add vyper==0.4.x

Ensure that you replace `0.4.x` with the version of ``vyper`` that is compatible with your project.
Check your ``pyproject.toml`` file for the required version of ``vyper``. For example:

.. code-block:: toml

    dependencies = ["moccasin==0.4.0", "vyper==0.4.1"]