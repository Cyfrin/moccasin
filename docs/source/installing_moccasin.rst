.. _install: 

###################
Installing Moccasin
###################

.. note:: Beginner Developers:

    Are you a new or beginner python developer? Then follow these steps:

    1. :ref:`Install uv <installation-with-uv>`

    2. :ref:`Install moccasin in an isolated environment <isolated_uv>`

    3. :ref:`Check to see if it worked <after_install>`

    4. :doc:`Go to the quickstart! <quickstart>`

There are a few things you'll need on your machine before you can install Moccasin. Please install the appropriate tools from the `Prerequisites`_ section. Once you have those, the recommended way to :ref:`install Moccasin is via uv <installation-with-uv>`.

.. contents::
   :depth: 3
   :local:


Prerequisites
#############

1. Python 3.11 or later

.. _installation-with-uv:

Installation with uv
====================

For those unfamiliar, `uv <https://docs.astral.sh/uv/>`_ is a fast python package manager that helps us install moccasin into it's own isolated virtual environment, so we don't get any weird dependency conflicts with other python packages. It's similar to `pip` and `pipx` if you've used them before. It even comes with some `pip` compatibility, will tools like `uv pip install`.

It's highly recommended you understand how `virtual environments <https://docs.python.org/3/library/venv.html>`_ work as well. 

The easiest way to install ``uv`` is:

.. tabs::

    .. code-tab:: bash linux / MacOS

        curl -LsSf https://astral.sh/uv/install.sh | sh

    .. tab:: Windows

        ``powershell -c "irm https://astral.sh/uv/install.ps1 | iex"``

        .. note:: 

            ⚠️ Windows users: We recommend you watch the first `10 minutes of this WSL tutorial <https://www.youtube.com/watch?v=xqUZ4JqHI_8>`_ and install and work with WSL. WSL stands for "Windows Subsystem for Linux" and it allows you to run a Linux commands on Windows machine. If you're working on WSL, you can just use the ``linux / MacOS`` command from the other tab.

But you can head over to the `uv installation instructions <https://docs.astral.sh/uv/getting-started/installation/>`_ for more options. If you don't have at least Python 3.11 installed, you'll need to install that first.

.. code-block:: bash

    uv python install 3.11

.. _isolated_uv:

Isolated Environment
--------------------

To install ``moccasin`` into an isolated environment with ``uv``, run:

.. code-block:: bash

    uv tool install moccasin

If you wish to install ``moccasin`` and use other python packages in your scripts, you'll use the ``with`` flag:

.. code-block:: bash

    uv tool install moccasin --with pandas

.. note::

    Installing ``moccasin`` into a virtual environment (via ``uv tools install`` or ``pipx install``) will require a different setup for injecting python packages. See :doc:`/core_concepts/dependencies/virtual_environments` for more information.

Then, go to :ref:`after installation <after_install>`.


Virtual Environment
-------------------

If instead, you'd prefer to have different ``mox`` executeables Or, if you want to have ``moccasin`` installed with a traditional virtual environment set, you can run:

.. code-block:: bash

    uv init
    uv venv
    source .venv/bin/activate

Then, you can install it as a uv installation:

.. code-block:: bash

    uv add moccasin

Where you'll be able to run the executeable with ``uv run mox`` instead of ``mox`` (see :ref:`after installation <after_install>`).

Or a pip installation:

.. code-block:: bash

    uv pip install moccasin

Where you'll be able to run the executeable with ``mox`` (see :ref:`after installation <after_install>`).


.. _installation-with-pipx:

Installation with pipx
======================

Pipx is a tool to help you install and run end-user applications written in Python. It's roughly similar to macOS's ``brew``, JavaScript's ``npx``, and Linux's ``apt``.

``pipx`` installs Moccasin into a virtual environment and makes it available directly from the commandline. Once installed, you will never have to activate a virtual environment prior to using Moccasin.

``pipx`` does not ship with Python. If you have not used it before you will probably need to install it.

You can either head over to the `pipx installation instructions <https://github.com/pipxproject/pipx>`_ or follow along below.

To install ``pipx``:

.. code-block:: bash

    python -m pip install --user pipx
    python -m pipx ensurepath

.. note::
    
    You may need to restart your terminal after installing `pipx`.

To install moccasin then with `pipx`:

.. code-block:: bash

    pipx install moccasin


.. note::

    Installing ``moccasin`` into a virtual environment (via ``uv tools install`` or ``pipx install``) will require a different setup for injecting python packages. See :doc:`/core_concepts/dependencies/virtual_environments` for more information.

Then, go to :ref:`after installation <after_install>`.

Installation with pip
=====================

You can install with ``pip``, and if you do so, it's highly recommended you understand how `virtual environments <https://docs.python.org/3/library/venv.html>`_ work. 

To install with `pip`:

.. code-block:: bash

    pip install moccasin
    
Then, go to :ref:`after installation <after_install>`.

From source 
===========

To install from source, you'll need the `uv tool installed <https://docs.astral.sh/uv/>`_. Once installed, you can run:

.. code-block:: bash

    git clone https://github.com/cyfrin/moccasin
    cd moccasin
    uv sync
    source .venv/bin/activate
    uv pip install -e .

And you will have ``mox`` in your virtual environment created from the ``uv`` tool. It's highly recommended you understand how `virtual environments <https://docs.python.org/3/library/venv.html>`_ work. 


Then, go to :ref:`after installation <after_install>`.

.. _after_install:

After installation
##################

Once installed, to verify that Moccasin is installed, you can run:

.. code-block:: bash

    mox --version

And see an output like:

.. code-block:: bash

    Moccasin CLI v0.1.0