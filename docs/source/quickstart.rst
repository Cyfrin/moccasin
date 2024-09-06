.. _quickstart: 

Quickstart
##########

Creating a new project 
======================

To create a new project, you can run the following command:

.. code-block:: bash

    gab init my_project

And this will create a new project in a new `my_project` directory. If you want to create a project in a directory that already has files/folders in it, run:

.. code-block:: bash

    gab init my_project --force

Let's check out the files and folders `gaboon` has created:

.. note::

    MacOS users may need to install `tree` with `brew install tree`.

Run the following commands:

.. code-block:: bash

    cd my_project
    tree .

You'll get an output like:

.. code-block:: console

    .
    ├── README.md
    ├── gaboon.toml
    ├── script
    │   ├── __init__.py
    │   └── deploy.py
    ├── src
    │   └── Counter.vy
    └── tests
        ├── conftest.py
        └── test_counter.py

This is a minimal project structure that `gaboon` creates. 

- `README.md` is a markdown file that you can use to describe your project.
- `gaboon.toml` is a configuration file that `gaboon` uses to manage the project.
- `script` is a directory that contains scripts that you can use to deploy your project.
- `src` is a directory that contains your vyper smart contracts.
- `tests` is a directory that contains your tests.


Deploying a contract 
====================

Now, unlike other frameworks, with `gaboon`, we never need to compile! Gaboon uses `titanoboa` under the hood to compile contracts quickly on the fly. Let's open our `deploy.py` file and look inside.

.. code-block:: python

    from src import Counter

    def deploy():
        counter = Counter.deploy()
        print("Starting count: ", counter.number())
        counter.increment()
        print("Ending count: ", counter.number())
        return counter

    def main():
        return deploy()

We can see a python script that will:

1. Deploy our `Counter` contract.
2. Print the starting count inside the contract.
3. Increment the count.
4. Print the ending count inside the contract.

We can run this script to the titanoboa pyevm (a local network that simulates ethereum) by running:

.. code-block:: bash

    gab run deploy

And we'll get an output like:

.. code-block:: console

    Running run command...
    Starting count:  0
    Ending count:  1

Awesome! This is how easy it is to run scripts with your smart contracts.

Running tests  
=============

Under the hood, `gaboon` uses `pytest <https://docs.pytest.org/en/7.1.x/contents.html>`_, and you can use a lot of your favorite pytest command line commands. If you just run:

.. code-block:: bash

    gab test

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