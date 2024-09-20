Virtual Environments
####################


When you want to add python packages to use in your scripts, you can of course install them normally into your environment.

.. code-block:: bash 

    # The "normal" python way
    pip install pandas 

    # The "cooler" way that we are going to teach you
    uv add pandas 

    # Another cool way
    poetry add pandas

    # This monstrous way
    uv pip install pandas 

We highly recommend that you setup a virtual environment for working with your python scripts. And our recommended method is with the ``uv`` tool. 

Working with uv 
===============

.. note::

    You can view the official `uv documentation <https://docs.astral.sh/uv/>`_ for more information.

To install, run:

.. code-block:: bash

    curl -LsSf https://astral.sh/uv/install.sh | sh

Then, in your ``moccasin`` project run:

.. code-block:: bash

    uv init

This will create a ``pyproject.toml`` which will manage your python dependencies. To add python packages to your project, you can run:

.. code-block:: bash

    uv add pandas

And your ``pyproject.toml`` will be updated with the new package. To work with your virtual environment, you can run:

.. code-block:: bash

    source .venv/bin/activate

And to deactivate:

.. code-block:: bash

    deactivate