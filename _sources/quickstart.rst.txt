.. _quickstart: 

Quickstart
##########

Creating a new project 
======================

To create a new project, you have different options:

.. tabs::

  .. tab:: VSCode & Pyproject

        .. code-block:: bash
            
            # Recommanded with VSCode and new projects
            mox init my_project --vscode --pyproject

  .. tab:: Pyproject

        .. code-block:: bash

            # Other IDEs and new projects
            mox init my_project --pyproject

  .. tab:: Simple

        .. code-block:: bash
            
            mox init my_project

And this will create a new project in a new ``my_project`` directory. 

.. tip::

    If you want to create a project in the current directory, you can use ``.`` as the project name:

    .. code-block:: bash

        mox init .

    This will create a new project in the current directory.
    
    If you want to create a project in a directory that already has files/folders in it, you can add the ``--force`` option to the command:

    .. code-block:: bash

        mox init my_project --force
    
    .. danger:: 

        This will overwrite any existing files/folders in the directory, so use it with caution!
    
Let's check out the files and folders ``moccasin`` has created:

.. note::

    MacOS users may need to install ``tree`` with ``brew install tree``. You can of course, just not install tree and skip this ``tree`` command.

Run the following commands:

.. code-block:: bash

    cd my_project
    tree .

You'll get an output like:

.. code-block:: console

    .
    ├── README.md
    ├── moccasin.toml
    ├── script
    │   ├── __init__.py
    │   └── deploy.py
    ├── src
    │   └── Counter.vy
    └── tests
        ├── conftest.py
        └── test_counter.py

This is a minimal project structure that ``moccasin`` creates. 

- ``README.md`` is a markdown file that you can use to describe your project.
- ``moccasin.toml`` is a configuration file that ``moccasin`` uses to manage the project.
- ``script`` is a directory that contains scripts that you can use to deploy your project.
- ``src`` is a directory that contains your vyper smart contracts.
- ``tests``` is a directory that contains your tests.

If you run ``tree . -a``, you'll also see the "hidden" files. 

- ``.gitignore`` is a file that tells git which files to ignore.
- ``.gitattributes`` is a file that tells git how to handle line endings.
- ``.coveragerc`` is a file that tells ``pytest`` how to handle coverage.


Let's look at the different options available to us when creating a new project.

.. _vscode-option:

VSCode option
-------------
    
.. hint::

    If you want to use the ``--vscode`` option, you need to have the `Vyper VSCode extension <https://marketplace.visualstudio.com/items?itemName=tintinweb.vscode-vyper>`_ installed.

The ``--vscode`` option will create a new project with a ``.vscode`` folder that contains a ``settings.json`` file. 

.. code-block:: console

    └── .vscode
        └── settings.json

This file contains settings that are specific to VSCode and will help you work with your project more easily.

.. code-block:: json

    {
        "files.exclude": {
            "**/__pycache__": true
        },
        "files.associations": {
            ".coveragerc": "toml"
        },
        "vyper.command": "vyper -p ./lib/github -p ./lib/pypi"
    }

.. tip::

    You can modify ``"vyper.command": "vyper -p ./lib/github -p ./lib/pypi"`` to chose which vyper compiler to use.
    For example, if you want to use the `vyper` compiler from your virtual environment, you can change it to:

    .. code-block:: json

        "vyper.command": "./.venv/bin/vyper -p ./lib/github -p ./lib/pypi"

.. _pyproject-option:

Pyproject option
----------------
The ``--pyproject`` option will create a new project with a ``pyproject.toml`` file.

.. code-block:: console

    └── pyproject.toml

This file is used to manage the project's dependencies and settings. It is a standard file used by many Python projects, and it is recommended to use it if you are using a package manager like `uv`.

.. hint::

    It is very useful when you want to use a specific version of a library, like `vyper` or `titanoboa` with moccasin. Check :ref:`Working with python dependencies doc <virtual_environments>` for more information.

.. _with-poetry:

With poetry
-------------


    
For ``poetry``, it is recommanded to use ``--force`` inside the subfolder of your project to get the moccasin architecture. For example, here it will be ``mox_project`` and not ``mox-project``

.. code-block:: console
    
    .
    ├── mox-project
    │   ├── mox_project


Deploying a contract 
====================

Now, unlike other frameworks, with ``moccasin``, we never need to compile! Moccasin uses ``titanoboa`` under the hood to compile contracts quickly on the fly. Let's open our ``deploy.py`` file and look inside.

.. code-block:: python

    from src import Counter

    def deploy():
        counter = Counter.deploy()
        print("Starting count: ", counter.number())
        counter.increment()
        print("Ending count: ", counter.number())
        return counter

    def moccasin_main():
        return deploy()

We can see a python script that will:

1. Deploy our ``Counter`` contract.
2. Print the starting count inside the contract.
3. Increment the count.
4. Print the ending count inside the contract.

We can run this script to the titanoboa pyevm (a local network that simulates ethereum) by running:

.. code-block:: bash

    mox run deploy

And we'll get an output like:

.. code-block:: console

    Running run command...
    Starting count:  0
    Ending count:  1

Awesome! This is how easy it is to run scripts with your smart contracts.

Running tests  
=============

Under the hood, ``moccasin`` uses `pytest <https://docs.pytest.org/en/7.1.x/contents.html>`_, and you can use a lot of your favorite pytest command line commands. If you just run:

.. code-block:: bash

    mox test

You'll get an output like:

.. code-block:: bash 

    Running test command...
    =================================== test session starts ===================================
    platform darwin -- Python 3.11.9, pytest-8.3.2, pluggy-1.5.0
    rootdir: /your/path/my_project
    plugins: cov-5.0.0, hypothesis-6.108.5, titanoboa-0.2.1
    collected 1 item                                                                          

    tests/test_counter.py .                                                             [100%]

    ==================================== 1 passed in 0.01s ====================================


.. note:: 

    If you want to add python dependencies to your ``moccasin`` project, see: :doc:`virtual environments documentation </core_concepts/dependencies/virtual_environments>`.

But that's it! You've now successfully gotten your first package up and going!