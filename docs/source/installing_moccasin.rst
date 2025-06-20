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

1. Python 3.11 or later ``(">= 3.11, <= 3.13")``

.. _installation-with-uv:

Installation with uv
====================

For those unfamiliar, `uv <https://docs.astral.sh/uv/>`_ is a fast python package manager that helps us install moccasin into it's own isolated virtual environment, so we don't get any weird dependency conflicts with other python packages. It's similar to ``pip`` and ``pipx`` if you've used them before. It even comes with some ``pip`` compatibility, will tools like ``uv pip install``.

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

.. hint::

    You can do the same with Python 3.12 or 3.13. Moccasin is currently only compatible with Python 3.11, 3.12, and 3.13.


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
    
    You may need to restart your terminal after installing ``pipx``.

To install moccasin then with ``pipx``:

.. code-block:: bash

    pipx install moccasin


.. note::

    Installing ``moccasin`` into a virtual environment (via ``uv tools install`` or ``pipx install``) will require a different setup for injecting python packages. See :doc:`/core_concepts/dependencies/virtual_environments` for more information.

Then, go to :ref:`after installation <after_install>`.

Installation with poetry
========================

Poetry is depedency management tool in Python. It allows to install/update libraries from your project, and also handle Python packaging.

``poetry`` installs dependencies into its default virtual environment ``{cache-dir}/virtualenvs`` related to the intialized project. See how `poetry virtual environment <https://python-poetry.org/docs/basic-usage/#using-your-virtual-environment>`_ works.

You can install Moccasin with ``poetry``, and if you do so, it's highly recommended you understand how `virtual environments <https://docs.python.org/3/library/venv.html>`_ work. 

You can either head over to the `poetry installation instructions <https://python-poetry.org/docs/#installation>`_ or follow along below.

To install ``poetry``, you'll need `pipx <https://github.com/pipxproject/pipx>`_:

.. code-block:: bash

    pipx install poetry

.. note::
    
    You may need to restart your terminal after installing ``poetry``.

Ensure ``poetry`` is available:

.. code-block:: bash

    poetry --version 
    # Poetry (version 2.0.1)

We'll need to initialize a ``poetry`` project to use its dedicated virtual enviroment to add Moccasin:

.. code-block:: bash

    poetry new mox-project
    cd mox-project

This will create the following directory structure for the ``mox-project`` dir:

.. code-block:: console

    .
    ├── mox-project
    │   ├── mox_project
    │   │   └── __init__.py
    │   ├── poetry.lock
    │   ├── pyproject.toml
    │   ├── README.md
    │   └── tests
    │       └── __init__.py

You can now navigate to the ``mox-project`` folder and install Moccasin:

.. code-block:: bash

    cd mox-project
    poetry add moccasin

.. caution::
    
    You may run into an issue where the default Python version registered in the ``pyproject.toml`` is not compatible with ``moccasin``. 
    
    .. code-block:: console 

        The current project's supported Python range (>=3.12) is not compatible with some of the required packages Python requirement:
        - moccasin requires Python <=3.13,>=3.11, so it will not be satisfied for Python >3.13

        Because no versions of moccasin match >0.3.6,<0.4.2
        and moccasin (0.3.6) requires Python <=3.13,>=3.11, moccasin is forbidden.
        So, because mox-project depends on moccasin (^0.3.6), version solving failed.


    To fix this you'll have to change manually the param ``requires-python``. For example: 

    .. code-block:: toml 

        [project]
        requires-python = ">=3.12,<=3.13"
    
    Adapt the python version at your convinience. You might need to redo ``poetry add moccasin`` until the error message from ``poetry is gone``

You can then activate your ``poetry`` env:

.. code-block:: bash
    
    eval $(poetry env activate)

Then, go to :ref:`after installation <after_install>`.

Installation with pip
=====================

You can install with ``pip``, and if you do so, it's highly recommended you understand how `virtual environments <https://docs.python.org/3/library/venv.html>`_ work. 

To install with ``pip``:

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