Scripting
#########

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

You can run the `deploy.py` script with either:

.. code-block:: bash

    mox run deploy

or

.. code-block:: bash

    mox run ./script/deploy.py

Importing from src 
==================

You can directly import contracts from the `src` folder into your scripts, and interact with them! Let's say you have a `Counter` contract in your `src` folder:

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

If you have :doc:`networks <networks>` defined in your :doc:`moccasin.toml <moccasin_toml>`, you can directly work with the network in your scripts. For example, if you have a `sepolia` network defined in your `moccasin.toml`:

.. code-block:: bash

    mox run deploy --network sepolia


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

You can see a list of arguments in the :doc:`moccasin reference documentation <all_moccasin_toml_parameters>` that you can run with your scripts.