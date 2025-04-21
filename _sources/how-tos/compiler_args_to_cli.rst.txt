How to pass vyper compiler args through the CLI 
###############################################

You don't! 

This is a bit of an anti-pattern that ``moccasin`` currently does not support. It is much safe to list your compiler args directly in the Vyper files themselves.

For example, if you wanted to pass the ``enable-decimals`` flag to the Vyper compiler, you would add the following line to the top of your Vyper file:

.. code-block:: python

    # pragma enable-decimals


The same way you define your ``pragma``` version.