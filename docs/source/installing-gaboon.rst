.. _install: 

Installing Gaboon
#################

There are a few things you'll need on your machine before you can install Gaboon. Please install the appropriate tools from the `Prerequisites`_ section. Once you have those, the recommended way to :ref:`install Gaboon is via uv <installation-with-uv>`.

Prerequisites
=============

1. Python 3.11 or later

.. _installation-with-uv:

Installation with uv
--------------------

For those unfamiliar, `uv <https://docs.astral.sh/uv/>`_ is a fast python package manager, and that helps us install gaboon into it's own isolated virtual environment, so we don't get any weird dependency conflicts with other python packages. It's similar to `pip` and `pipx` if you've used them before. It even comes with some `pip` compatibility, will tools like `uv pip install`.

It's highly recommended you understand how `virtual environments <https://docs.python.org/3/library/venv.html>`_ work as well. 

The easiest way to install `uv` is:

.. code-block:: bash

    curl -LsSf https://astral.sh/uv/install.sh | sh

But you can head over to the `uv installation instructions <https://docs.astral.sh/uv/getting-started/installation/>`_ for more options.


Then, to install gaboon with `uv`, run:

.. code-block:: bash

    uv tool install gaboon

Once installed, to verify that Gaboon is installed, you can run:

.. code-block:: bash

    gab --version

And see an output like:

.. code-block:: bash

    Gaboon CLI v0.1.0

.. _installation-with-pipx:

Installation with pipx
----------------------

Pipx is a tool to help you install and run end-user applications written in Python. It's roughly similar to macOS's ``brew``, JavaScript's ``npx``, and Linux's ``apt``.

``pipx`` installs Gaboon into a virtual environment and makes it available directly from the commandline. Once installed, you will never have to activate a virtual environment prior to using Gaboon.

``pipx`` does not ship with Python. If you have not used it before you will probably need to install it.

You can either head over to the `pipx installation instructions <https://github.com/pipxproject/pipx>`_ or follow along below.

To install ``pipx``:

.. code-block:: bash

    python -m pip install --user pipx
    python -m pipx ensurepath

.. note::
    
    You may need to restart your terminal after installing `pipx`.

To install gaboon then with `pipx`:

.. code-block:: bash

    pipx install gaboon

Once installed, you can run the following command to verify that Gaboon is installed:

.. code-block:: bash

    gab --version

And see an output like:

.. code-block:: bash

    Gaboon CLI v0.1.0

Installation with pip
---------------------

You can install with `pip`, and if you do so, it's highly recommended you understand how `virtual environments <https://docs.python.org/3/library/venv.html>`_ work. 

To install with `pip`:

.. code-block:: bash

    pip install gaboon

From source 
-----------

To install from source, you'll need the `uv tool installed <https://docs.astral.sh/uv/>`_. Once installed, you can run:

.. code-block:: bash

    git clone https://github.com/vyperlang/gaboon
    cd gaboon
    uv sync
    source .venv/bin/activate
    uv pip install -e .

And you will have `gab` in your virtual environment created from the `uv` tool. It's highly recommended you understand how `virtual environments <https://docs.python.org/3/library/venv.html>`_ work. 
