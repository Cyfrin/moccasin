.. _virtual_environments:

Python packages in your scripts 
###############################

When you want to add python packages to use in your scripts, it depends on how you installed ``moccasin``. 

In an isolated environment (``uv tool install`` or ``pipx install``)
--------------------------------------------------------------------

If you installed ``moccasin`` with the ``uv tool install`` or ``pipx install``, you can re-install your ``moccasin`` installation using the ``--with`` flag to "inject" the python packages you want to use.


.. tabs::

    .. code-tab:: bash uv

        # This will reinstall moccasin with pandas
        uv tool install moccasin --with pandas
    
    .. code-tab:: bash pipx

        # With pipx you don't need to reinstall, you'll just "inject" the python packages you want to use.
        pipx inject moccasin pandas


In a virtual environment (``uv pip install``, ``uv add``, or ``pip install``)
-----------------------------------------------------------------------------

Let's say you have setup a virtual environment:

.. tabs::

    .. code-tab:: bash uv 

        uv init
        uv venv
        source .venv/bin/activate
    
    .. code-tab:: bash pip / python

        python -m venv .venv
        source .venv/bin/activate
    
    .. code-tab:: bash poetry

        poetry init
        poetry shell

.. note::

    Remember, to deactivate run:

    .. code-block:: bash
        
        deactivate


You can install python packages as you'd expect:

.. tabs::

    .. code-tab:: bash uv

        uv add pandas

    .. code-tab:: bash uv-pip

        uv pip install pandas
    
    .. code-tab:: bash pip

        pip install pandas
    
    .. code-tab:: bash poetry

        poetry add pandas

.. note::

    If you installed ``moccasin`` with ``uv add moccasin`` you'll only be able to use these packages with ``uv run mox``. If you want to use the ``mox`` command in your virtual environment, you'll need to install ``moccasin`` with ``uv pip install moccasin``.

We highly recommend that you setup a virtual environment or injecting packages into your mox isolated environment for working with your python scripts. And our recommended method is with the ``uv`` tool. 