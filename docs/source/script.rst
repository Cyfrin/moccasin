Scripting
#########

Scripts are ways to deploy and work with contracts. You can either reference them by path or by name. For example, if your directory looks like this:

.. code-block:: bash

    .
    ├── README.md
    ├── gaboon.toml
    ├── script
    │   └── deploy.py
    ├── src
    │   └── Counter.vy
    └── tests
        ├── conftest.py
        └── test_counter.py

You can run the `deploy.py` script with either:

.. code-block:: bash

    gab run deploy

or

.. code-block:: bash

    gab run ./script/deploy.py

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

If you have :doc:`networks <networks>` defined in your :doc:`gaboon.toml <gaboon_toml>`, you can directly work with the network in your scripts. For example, if you have a `sepolia` network defined in your `gaboon.toml`:

.. code-block:: bash

    gab run deploy --network sepolia


gaboon_main
===========

In your scripts, the `gaboon_main` function is special, if you have a function with this name in your script, `gaboon` will run this function by default after running the script like a regular python file. For example, you could also do this:

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

    def gaboon_main():
        deploy()

You can see a list of arguments in the :doc:`gaboon reference documentation <all_gaboon_toml_parameters>` that you can run with your scripts.