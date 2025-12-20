Fixtures 
########

What are fixtues?
=================

Fixtures in ``pytest`` are functions that provide a fixed baseline or setup that your tests can use to operate in a controlled and predictable environment. They are used to define resources or state that will be used by the tests. Examples include setting up a database connection, creating a temporary file, initializing test data, or configuring environment variables.

.. note::

    For more information on fixtures in ``pytest`` we recommend reading the `pytest documentation <https://docs.pytest.org/en/6.2.x/fixture.html>`_ or asking an AI chat bot. 


Using Fixtures 
==============

Defining fixtures in your tests is one of the best ways to make sure your tests are fast and reliable. 

In a ``conftest.py`` file in your ``tests`` directory, you'd make something like this:

.. code-block:: python 

    from script.mock_deployer.deploy_feed import deploy_feed

    @pytest.fixture(scope="session")
    def price_feed():
        return deploy_feed()

Then, you can use these fixtures in your tests:

.. code-block:: python 

    def test_using_fixtures(price_feed):
        assert price_feed is not None
