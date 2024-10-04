Fixtures 
########

What are fixtues?
=================

Fixtures in ``pytest`` are functions that provide a fixed baseline or setup that your tests can use to operate in a controlled and predictable environment. They are used to define resources or state that will be used by the tests. Examples include setting up a database connection, creating a temporary file, initializing test data, or configuring environment variables.

.. note::

    For more information on fixtures in ``pytest`` we recommend reading the `pytest documentation <https://docs.pytest.org/en/6.2.x/fixture.html>`_ or asking an AI chat bot. 

One of the most powerful features of ``moccasin`` is the ability to define fixtures that can be used across multiple tests. 


Using Fixtures 
==============

Fixtures are just :doc:`NamedContracts </core_concepts/named_contracts>` with the ``fixture`` flag set to ``True``.

.. code-block:: toml 

    [networks.contracts]
    price_feed = { deployer_script = "mock_deployer/deploy_feed.py", fixture = true }

If you setup a ``NamedContract`` as a fixture, you can ``request`` it in your tests. Ideally, you'd place this code in a ``conftest.py`` file in your ``tests`` directory.

.. code-block:: python 

    request_fixtures(["price_feed"], scope="session")

This is roughly equivalent to doing:

.. code-block:: python 

    from script.mock_deployer.deploy_feed import deploy_feed

    @pytest.fixture(scope="session")
    def price_feed():
        return deploy_feed()

You can also renamed a named fixture, for example if you have multiple ERC20 contracts you want to give different names to:

.. code-block:: python 

    # This will create 2 fixtures, on named "usdc" and one "dai" but they will both use the same erc20 deploy script or abi
    request_fixtures([ ("erc20", "usdc"), ("erc20", "dai")], scope="session")

Then, you can use these fixtures in your tests:

.. code-block:: python 

    def test_using_fixtures(usdc, dai):
        assert usdc.address is not None
        assert dai.decimals() > 0
