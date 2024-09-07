Project Layout 
##############

A typical gaboon project is structured as follows:

.. code-block:: bash

    .
    ├── README.md
    ├── gaboon.toml
    ├── script/
    ├── src/
    ├── tests/
    └── out/

Where:

- `README.md` is a markdown file that you can use to describe your project.
- `gaboon.toml` is a configuration file that `gaboon` uses to manage the project.
- `script` is a directory that contains python scripts that you can use to deploy your project.
- `src` is a directory that contains your vyper smart contracts.
- `tests` is a directory that contains your tests.
- `out` is an optional directory that contains the compiled contracts. In gaboon and titanoboa, contracts are compiled on the fly!

Changing your layout 
====================

If you wanted to adjust your contracts location, for example, have your smart contracts folder be named `contracts` instead of `src`, you'd update your `gaboon.toml` file to reflect this change:

.. code-block:: toml

    [layout]
    src = "contracts"


