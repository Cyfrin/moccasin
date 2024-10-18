Gas Profiling
#############

.. note:: See the `titanoboa gas-profiling documentation for more information. <https://titanoboa.readthedocs.io/en/latest/testing.html#gas-profiling>`_

`moccasin` has a built in gas profiler that can be used to profile your contracts gas usage. It uses `titanoboa's <https://titanoboa.readthedocs.io/en/latest/testing.html#gas-profiling>`_ gas profiling under the hood. 

To use the gas profiler, you can run:

.. code-block:: bash 

    mox test --gas-profile

And get an output like:

.. code-block:: bash 

    ┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━┳━━━━━━━━┳━━━━━━━┳━━━━━┳━━━━━┓
    ┃ Contract    ┃ Address                                    ┃ Computation ┃ Count ┃ Mean ┃ Median ┃ Stdev ┃ Min ┃ Max ┃
    ┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━╇━━━━━━━━╇━━━━━━━╇━━━━━╇━━━━━┩
    │ FooContract │ 0x0000000000000000000000000000000000000066 │ foo         │ 1     │ 88   │ 88     │ 0     │ 88  │ 88  │
    └─────────────┴────────────────────────────────────────────┴─────────────┴───────┴──────┴────────┴───────┴─────┴─────┘


    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━┓
    ┃ Contract                                             ┃ Computation                                                                ┃ Count ┃ Mean  ┃ Median ┃ Stdev ┃ Min   ┃ Max   ┃
    ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━┩
    │ Path:                                                │                                                                            │       │       │        │       │       │       │
    │ Name: FooContract                                    │                                                                            │       │       │        │       │       │       │
    │ Address: 0x0000000000000000000000000000000000000066  │                                                                            │ Count │ Mean  │ Median │ Stdev │ Min   │ Max   │
    │ ---------------------------------------------------- │ -------------------------------------------------------------------------- │ ----- │ ----- │ -----  │ ----- │ ----- │ ----- │
    │ Function: foo                                        │   4: def foo(a: uint256 = 0):                                              │ 1     │ 73    │ 73     │ 0     │ 73    │ 73    │
    │                                                      │   5: x: uint256 = a                                                        │ 1     │ 15    │ 15     │ 0     │ 15    │ 15    │
    └──────────────────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────┴───────┴───────┴────────┴───────┴───────┴───────┘