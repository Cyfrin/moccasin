.. image:: _static/mark.svg
    :width: 140px
    :alt: Moccasin logo
    :align: center


Moccasin
########

Moccasin is a fast, pythonic smart contract development framework heavily powered by `titanoboa <https://github.com/vyperlang/titanoboa>`_.

.. note::

   This project is under active development.

.. code-block:: console 
     
    usage: Moccasin CLI [-h] [-d] [-q]
                    {init,compile,build,test,run,script,deploy,wallet,console,install,purge,config,explorer,inspect,deployments,utils,u,util} ...

    🐍 Pythonic Smart Contract Development Framework

    positional arguments:
    {init,compile,build,test,run,script,deploy,wallet,console,install,purge,config,explorer,inspect,deployments,utils,u,util}
        init                Initialize a new project.
        compile (build)     Compiles the project.
        test                Runs all tests in the project.
        run (script)        Runs a script with the project's context.
        deploy              Deploys a contract named in the config with a deploy script.
        wallet              Wallet management utilities.
        console             BETA, USE AT YOUR OWN RISK: Interact with the network in a python shell.
        install             Installs the project's dependencies.
        purge               Purge a given dependency
        config              View the Moccasin configuration.
        explorer            Work with block explorers to get data.
        inspect             Inspect compiler data of a contract.
        deployments         View deployments of the project from your DB.
        utils (u, util)     Helpful utilities - right now it's just the one.

    options:
    -h, --help            show this help message and exit
    -d, --debug           Run in debug mode
    -q, --quiet           Suppress all output except errors

How to read the documentation
=============================

The moccasin documentation is written in a way that assumes you are on a MacOS or Linux-like system. If you are using windows, we recommend you watch the first `10 minutes of this WSL tutorial <https://www.youtube.com/watch?v=xqUZ4JqHI_8>`_ and work with WSL. WSL stands for "Windows Subsystem for Linux" and it allows you to run a Linux commands on Windows machine.


TOML Formatting
---------------

In TOML you can think of each section as a giant JSON object. Each of these are essentially identical:

+----------------------------------+----------------------------------+----------------------------------+
| TOML (Expanded)                  | TOML (Compact)                   | JSON                             |
+==================================+==================================+==================================+
| .. code-block:: toml             | .. code-block:: bash             | .. code-block:: json             |
|                                  |                                  |                                  |
|    [project]                     |    [project]                     |    {                             |
|    src = "contracts"             |    src = "contracts"             |      "project": {                |
|                                  |    networks = {                  |        "src": "contracts",       |
|    [project.networks.sepolia]    |      sepolia = {                 |        "networks": {             |
|    url = "https://..."           |        url = "https://...",      |          "sepolia": {            |
|    chain_id = 11155111           |        chain_id = 11155111       |            "url": "https://...", |
|                                  |      },                          |            "chain_id": 11155111  |
|    [project.networks.zksync]     |      zksync = {                  |          },                      |
|    url = "https://..."           |        url = "https://...",      |          "zksync": {             |
|    chain_id = 324                |        chain_id = 324            |            "url": "https://...", |
|                                  |      }                           |            "chain_id": 324       |
|                                  |    }                             |          }                       |
|                                  |                                  |        }                         |
|                                  |                                  |      }                           |
|                                  |                                  |    }                             |
+----------------------------------+----------------------------------+----------------------------------+

Why Moccasin?
=============

We think web3 needs the following:

1. A python smart contract development framework.
    a. We need this because python is the 2nd most popular language on earth, and is the number one choice for artificial intelligence and new computer engineers!
2. An easy way to run devops on contracts.
    a. Running scripts to interact with contracts needs to be easy in a language that humans can understand.
3. And finally... it needs to be fast!

Then, we have some fun plans for AI, formal verification, fuzzing, and more in the future of moccasin, so stay tuned!


Head over to :doc:`installing moccasin <installing_moccasin>` to get started.