Testing
####### 

``moccasin`` uses ``pytest`` under the hood, so you can setup your tests like regular ``titanoboa`` based python tests.

.. code-block:: python 

    def test_increment_one(counter_contract):
        counter_contract.increment()
        assert counter_contract.number() == 2


    def test_increment_two(counter_contract):
        counter_contract.increment()
        counter_contract.increment()
        assert counter_contract.number() == 3

And run all your tests with ``mox test``, to get an output like:

.. code-block:: console 

    Running test command...
    ====================================== test session starts =======================================
    platform darwin -- Python 3.11.6, pytest-8.3.3, pluggy-1.5.0
    rootdir: ~/code/moccasin
    configfile: pyproject.toml
    plugins: cov-5.0.0, titanoboa-0.2.2, hypothesis-6.112.0
    collected 3 items                                                                                

    tests/test_counter.py ..                                                                   [ 66%]
    tests/test_fork_usdc.py .                                                                  [100%]

    ======================================= 3 passed in 0.01s ========================================

This is the most basic setup for testing. 

You can additionally use `pytest-xdist <https://pytest-xdist.readthedocs.io/en/stable/>`_ to run your tests in a multi-threaded environment.

.. code-block:: console 

    mox test -n auto

    Running test command...
    =========================================================== test session starts ============================================================
    platform darwin -- Python 3.11.6, pytest-8.3.3, pluggy-1.5.0
    rootdir: ~/code/moccasin
    configfile: pyproject.toml
    plugins: titanoboa-0.2.5b1, cov-5.0.0, hypothesis-6.115.2, xdist-3.6.1
    16 workers [2 items]      
    ..                                                                                                                                   [100%]
    ============================================================ 2 passed in 2.40s =============================================================


.. toctree::
    :maxdepth: 2

    Gas Profiling <testing/gas_profiling.rst>
    Coverage <testing/coverage.rst>
    Fixtures <testing/fixtures.rst>
    Testing with boa <testing/titanoboa_testing.rst>
    How to prank <testing/pranking.rst>
    Staging Markers <testing/staging_markers.rst>
    Fuzzing <testing/fuzzing.rst>
    