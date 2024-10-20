Scripting
#########

.. contents::
   :depth: 3
   :local:


Help command
============

.. code-block:: console 

     mox run --help
    usage: Moccasin CLI run [-h] [-d] [-q] [--fork [FORK]] [--network NETWORK | --url URL | --prompt-live [PROMPT_LIVE]]
                            [--account ACCOUNT | --private-key PRIVATE_KEY] [--password PASSWORD | --password-file-path PASSWORD_FILE_PATH]
                            script_name_or_path

    Runs a script with the project's context.

    positional arguments:
    script_name_or_path   Name of the script in the script folder, or the path to your script.

    options:
    -h, --help            show this help message and exit
    -d, --debug           Run in debug mode
    -q, --quiet           Suppress all output except errors
    --fork [FORK]
    --network NETWORK     Alias of the network (from the moccasin.toml).
    --url URL, --rpc URL  RPC URL to run the script on.
    --prompt-live [PROMPT_LIVE]
                            Prompt the user to make sure they want to run this script.
    --account ACCOUNT     Keystore account you want to use.
    --private-key PRIVATE_KEY
                            Private key you want to use to get an unlocked account.
    --password PASSWORD   Password for the keystore account.
    --password-file-path PASSWORD_FILE_PATH
                            Path to the file containing the password for the keystore account.


Scripting with Moccasin 
=======================


Scripts are ways to deploy and work with contracts. You can either reference them by path or by name. For example, if your directory looks like this:

.. code-block:: bash

    .
    ├── README.md
    ├── moccasin.toml
    ├── script
    │   └── deploy.py
    ├── src
    │   └── Counter.vy
    └── tests
        ├── conftest.py
        └── test_counter.py

You can run the ``deploy.py`` script with either:

.. code-block:: bash

    mox run deploy

or

.. code-block:: bash

    mox run ./script/deploy.py

Importing from src 
==================

You can directly import contracts from the ``src`` folder into your scripts, and interact with them! Let's say you have a ``Counter`` contract in your ``src`` folder:

.. code-block:: python

    from src import Counter

    def deploy():
        counter = Counter.deploy()
        print("Starting count: ", counter.number())
        counter.increment()
        print("Ending count: ", counter.number())
        return counter

    deploy()

Networking 
==========

If you have :doc:`networks <networks>` defined in your :doc:`moccasin.toml <moccasin_toml>`, you can directly work with the network in your scripts. For example, if you have a `sepolia` network defined in your ``moccasin.toml``:

.. code-block:: bash

    mox run deploy --network sepolia

You can learn more about networks in the :doc:`networks documentation <networks>`.


moccasin_main
=============

In your scripts, the `moccasin_main` function is special, if you have a function with this name in your script, `moccasin` will run this function by default after running the script like a regular python file. For example, you could also do this:

.. code-block:: python

    from src import Counter

    def deploy():
        counter = Counter.deploy()
        print("Starting count: ", counter.number())
        counter.increment()
        print("Ending count: ", counter.number())
        return counter

    deploy()

And it would do the same as the following. 

.. code-block:: python

    from src import Counter

    def deploy():
        counter = Counter.deploy()
        print("Starting count: ", counter.number())
        counter.increment()
        print("Ending count: ", counter.number())
        return counter

    def moccasin_main():
        deploy()

You can see a list of arguments in the :doc:`moccasin reference documentation </all_moccasin_toml_parameters>` that you can run with your scripts.

Working with dependencies
=========================

There are two kinds of dependencies you can work with in your moccasin project:

- :doc:`Smart Contract dependencies <dependencies>`: For contracts that you want to use packages from. 
- :doc:`Python dependencies </core_concepts/dependencies/virtual_environments>`: For python packages that you want to use in your scripts.

Each have their own respective documentation. 

.. toctree::
    :maxdepth: 3

    scripting/console.rst
    scripting/deploy.rst
