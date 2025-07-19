1.1 Setup ZKsync tools
======================

To work with ZKsync, you need to set up your environment properly.
This includes installing necessary tools to compile and deploy smart contracts.

Here is quick quote from the `ZKsync documentation <https://docs.zksync.io/zksync-protocol/evm-interpreter/overview>`_
about their virtual machine:

    `ZKsync chains like Era operate on EraVM,
    a ZK-optimized virtual machine that differs
    from the Ethereum Virtual Machine (EVM)
    in its instruction set and execution model.
    While Solidity and Vyper can be compiled to EraVM bytecode,
    differences in execution and tooling have
    required modifications in some cases.`

.. note::

    At the time of writing, they are now fully EVM compatible, so you can
    compile and deploy without using their specific virtual machine. But
    it's better to use the EraVM bytecode for optimal performance.

Since it could be a bit tricky to set up the tools,
this tutorial will help you to install
``anvil-zksync`` and ``zkvyper`` to ensure
you can compile and deploy smart contracts to ZKsync Era.

Install anvil-zksync
----------------------

This is the easiest to install since we are going
to use ``foundryup-zksync`` to install it. You can check
the `foundryup-zksync documentation <https://foundry-book.zksync.io/getting-started/installation>`_
for more information.

To install it, run the following command:

.. code-block:: bash

    curl -L https://raw.githubusercontent.com/matter-labs/foundry-zksync/main/install-foundry-zksync | bash

    # To update your terminal
    source ~/.bashrc

.. tip::

    You can also use your preferred shell to run the command. Like ``| zsh``
    with ``source ~/.zshrc`` if you are using Zsh.

.. hint::

    You can check the content of the script before running it.
    Just go to the `install-foundry-zksync <https://raw.githubusercontent.com/matter-labs/foundry-zksync/main/install-foundry-zksync>`_.
    Or you can run the command with ``| less`` to see the content
    before running it, like this:

    .. code-block:: bash

        curl -L https://raw.githubusercontent.com/matter-labs/foundry-zksync/main/install-foundry-zksync | less




And you should be good to go! You can check if it is installed correctly
by running the following command:

.. code-block:: bash

    anvil-zksync --version

    # You should see the version of anvil-zksync installed
    # anvil-zksync 0.6.9 (or similar)

Install zkvyper
----------------

``zkvyper`` is the compiler for Vyper to compile to ZKsync Era bytecode. And it's
maintained by the `Matter Labs <https://matter-labs.io/>`_ team.

It should be the most tricky part to install. If you want
to check by yourself, you can check the zkvyper Github repository `era-compiler-vyper <https://github.com/matter-labs/era-compiler-vyper>`_.

If you plan to contribute and dive into the code of ``zkvyper``, you can
follow along with their `doc <https://matter-labs.github.io/era-compiler-vyper/latest/01-installation.html>`_.
But for most developers, you can use the **static executable**
provided by the team on their `GitHub releases page <https://github.com/matter-labs/era-compiler-vyper/releases>`_.

Since it could be difficult to understand how to install it,
we will provide the simplest way to install it.
Just follow these steps:

Choose the right version for your system
########################################

At the time of writing, the latest version is ``v1.5.11``.

.. note::

    Adapt the version number to the latest one available if you
    are reading this in the future.

If you check their release page, you will see several files
like this:

.. code-block:: text

    zkvyper-linux-amd64-gnu-v1.5.11
    zkvyper-linux-amd64-musl-v1.5.11
    zkvyper-linux-arm64-gnu-v1.5.11
    zkvyper-linux-arm64-musl-v1.5.11
    zkvyper-macosx-amd64-v1.5.11
    zkvyper-macosx-arm64-v1.5.11
    zkvyper-macosx-v1.5.11
    zkvyper-windows-amd64-gnu-v1.5.11.exe

Each file corresponds to a different:

- **Operating system** (Linux, macOS, Windows)
- **Architecture** (amd64, arm64)
- **C library** (gnu, musl)

If you are not sure which one to choose, you can check your architecture
by running the following command:

.. code-block:: bash

    uname -m

    # x86_64

- If you see ``x86_64``, you should choose the ``amd64`` version.
- If you see ``aarch64``, you should choose the ``arm64`` version.

And check you system's C library by running:

.. code-block:: bash

    ldd --version

    # ldd (Ubuntu GLIBC 2.35-0ubuntu3.10) 2.35

- If you see ``GLIBC``, you should choose the ``gnu`` version.
- Else you should choose the ``musl`` version.

.. tip::

    You can also follow along with an AI assistant to help you
    uncover the right version for your system. It will guide
    you through the process **BUT** always double-check.


This will give you information about your system, including the architecture
and the operating system.

Mine is therefore ``zkvyper-linux-amd64-gnu-v1.5.11``.

Download and setup zkvyper
##########################

Now that you have the right version, you can download it.

1. Use the following command to download it:

.. code-block:: bash

    curl -L https://github.com/matter-labs/era-compiler-vyper/releases/download/1.5.11/zkvyper-linux-amd64-gnu-v1.5.11 -o zkvyper

.. hint::

    You can also use ``wget`` if you prefer it over ``curl``.

2. Check if the file is there:

.. code-block:: bash

    ls -l zkvyper

    # -rw-rw-r-- 1 s3bc40 s3bc40 42448112 Jul 19 17:19 zkvyper


3. Make the file executable:

.. code-block:: bash

    chmod +x zkvyper
    ls -l zkvyper

    # -rwxrwxr-x 1 s3bc40 s3bc40 42448112 Jul 19 17:19 zkvyper

4. Move the file to a directory in your ``$PATH``.
   For example, you can move it to ``/usr/local/bin``:

.. code-block:: bash

    sudo mv zkvyper /usr/local/bin/

5. Check if it is installed correctly by running:

.. code-block:: bash

    source ~/.bashrc
    # or source ~/.zshrc if you are using Zsh
    # or just open a new terminal

    zkvyper --version

    # Vyper compiler for ZKsync v1.5.11 (LLVM build 6fe1b2dbfe325be4977538ad709cc67ef972fbac)

Now you have successfully installed ``zkvyper`` and ``anvil-zksync``!
You can now compile and deploy smart contracts to ZKsync Era.

Next steps, you'll learn how initialize a new project
with Moccasin!
