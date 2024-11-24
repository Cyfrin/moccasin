Juypter Notebooks (IPython)
###########################

If you want to run a Jupyter notebook with all the setup a script has (named contracts, ``sys.path`` adjustments, etc), you can use the following code:

.. code-block:: python

    from moccasin import setup_notebook

    setup_notebook()

Then, you can work with the notebook as you would normally.

.. code-block:: python 

    from moccasin.config import get_active_network

    active_network = get_active_network()
    eth_usd = active_network.manifest_named("eth_usd_price_feed")


If you update your config while the notebook is running, you can reload the config with:

.. code-block:: python

    from moccasin.config import get_config

    config = get_config()
    # This command
    config.reload()