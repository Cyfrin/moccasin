Removing Dependencies (Purge)
#############################

To remove a dependency from both:

- Your project (your ``lib`` folder)
- Your ``moccasin.toml`` file


You can use the :doc:`purge </cli_reference/purge>` command. 

Removing a pypi/pip dependency
------------------------------

To remove a pypi/pip dependency, you can run the following:

.. code-block:: bash

    mox purge PACKAGE_NAME

And it will be removed from your:

- ``lib`` folder
- ``moccasin.toml`` file

Removing a GitHub dependency
----------------------------

To remove a GitHub dependency, you can run the following:

.. code-block:: bash

    mox purge ORG/REPO

And it will be removed from your:

- ``lib`` folder
- ``moccasin.toml`` file
