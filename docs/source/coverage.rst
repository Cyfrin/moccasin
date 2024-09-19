Coverage
########

.. note:: See the `titanoboa gas-profiling documentation for more information. <https://titanoboa.readthedocs.io/en/latest/testing.html#coverage>`_


You can also run coverage tests, using the ``--coverage`` flag, and any flag the comes with `pytest-cov <https://pypi.org/project/pytest-cov/>`_. This also uses `titanoboa <https://titanoboa.readthedocs.io/en/latest/testing.html#coverage>`_ under the hood. 

To run coverage tests, you can run:

.. code-block:: bash 

    mox test --coverage

And get an output like:

.. code-block:: bash

    ---------- coverage: platform darwin, python 3.11.6-final-0 ----------
    Name                                  Stmts   Miss Branch BrPart  Cover   Missing
    ---------------------------------------------------------------------------------
    contracts/Counter.vy                      2      1      0      0    50%   9
    contracts/mocks/MockV3Aggregator.vy      16      8      0      0    50%   34-50
    script/__init__.py                        0      0      0      0   100%
    script/deploy.py                         10      1      0      0    90%   14
    script/deploy_coffee.py                  11      6      0      0    45%   7-11, 15
    script/get_usdc_balance.py                9      9      0      0     0%   1-14
    script/mock_deployer/deploy_feed.py       8      0      0      0   100%
    script/quad_manifest.py                  14     14      0      0     0%   1-24
    ---------------------------------------------------------------------------------
    TOTAL                                    70     39      0      0    44%

You'll notice the ``script``\s are included by default, this is intentional. You can setup configuration for coverage in a ``.coveragerc`` file, or select a different configuration file by setting it in your ``moccasin.toml``.

.. code-block:: toml 

    [project]
    cov_config = ".coveragerc"
