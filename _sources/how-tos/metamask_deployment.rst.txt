Deploy with MetaMask Prompts
############################

Moccasin provides a convenient way to deploy your smart contracts through MetaMask prompts using the ``--prompt-metamask`` flag. This feature starts a local server that interfaces with MetaMask for contract deployment.

1. Prerequisites
================

Before using the MetaMask deployment feature, ensure:

- You have MetaMask installed in your browser
- Your MetaMask wallet is set up and connected to the desired network
- Your moccasin project is properly configured

2. Deploy with MetaMask prompts
===============================

To deploy contracts using MetaMask prompts, use the ``--prompt-metamask`` flag with your deployment script:

.. code-block:: bash

    mox run deploy_script.py --prompt-metamask

This command will:

1. Start a local server
2. Open your default browser (or provide a URL to visit)
3. Interface with MetaMask for transaction signing
4. Deploy your contracts through MetaMask prompts

3. Example deployment script
============================

Here's an example of how your deployment script might look:

.. code-block:: python

    def moccasin_main():
        # Deploy your contract
        my_contract = MyContract.deploy()
        print(f"Contract deployed at: {my_contract.address}")
        
        # Interact with the contract
        my_contract.some_function()
        print("Contract interaction completed")

4. Network configuration
========================

Make sure your ``moccasin.toml`` is configured with the appropriate network settings:

.. code-block:: toml

    [networks.mainnet]
    url = "https://mainnet.infura.io/v3/YOUR_PROJECT_ID"
    chain_id = 1

    [networks.sepolia]
    url = "https://sepolia.infura.io/v3/YOUR_PROJECT_ID"
    chain_id = 11155111

5. Run the deployment
=====================

Execute your deployment script with the MetaMask prompt flag:

.. code-block:: bash

    mox run deploy_script.py --network sepolia --prompt-metamask

MetaMask will prompt you to confirm each transaction during the deployment process.