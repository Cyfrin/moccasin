# Moccasin Multisig CLI

This module provides a command-line interface for building, signing, and broadcasting Safe multisig transactions and messages. It is designed for both interactive use and automation, making it suitable for offline developer workflows.

# Moccasin Multisig CLI

This module provides a command-line interface for building, signing, and broadcasting Safe multisig transactions and messages. It is designed for both interactive use and automation, making it suitable for offline developer workflows.

## Features

- **Interactive Transaction Builder (`tx-build`):**

  - Build Safe multisig transactions with prompts for all required fields.
  - Supports both single transactions and batch (MultiSend) operations.
  - Gas estimation is performed automatically or interactively, including SafeTx gas, base gas, and gas price, with validation of contract balance and nonce.
  - Input validation for addresses, calldata, and other parameters. Defaults and scripted values supported if arguments are omitted.
  - MultiSend support for batching multiple internal transactions.
  - EIP-712 structured data output for signing and verification.

> Note: SafeTxGas estimation is automatically performed for single transactions. For MultiSend batches, it is not automatically estimated due to complexity, but can be done interactively.

The CLI will prompt for these values or set sensible defaults if omitted.

- **Transaction Signing (`tx-sign`):**

  - Sign Safe multisig transactions from EIP-712 JSON, with strict domain validation and owner checks.
  - Prompts for signer account (keystore or private key) and password if needed.
  - Validates signer is a Safe owner and has not already signed the transaction.
  - Displays SafeTx details and enforces owner/domain checks before signing.
  - Interactive confirmation before signing, with ordered display of signers.

- **Transaction Broadcasting (`tx-broadcast`):**

  - Broadcast signed Safe multisig transactions to the blockchain.
  - Prompts for broadcaster account (keystore or private key) and password if needed.
  - Validates SafeTx has not already been broadcasted and has enough signers (threshold check).
  - Checks Safe contract balance and funds for gas before broadcasting.
  - Displays estimated cost in wei and SafeTx details before broadcasting.
  - Interactive confirmation before broadcasting, with display of transaction hash and broadcasted transaction details.

- **Input Validation:**

  - All commands validate input parameters and prompt interactively for missing values.
  - JSON file validation for input/output.

- **Extensible CLI:**

  - Modular design for future commands and integration with external tools.
  - All prompts are branded and support autosuggest for convenience.

## CLI Commands

### `mox msig tx-build`

Build a Safe multisig transaction interactively or via command-line arguments.

**Arguments:**

- `--url` or `--rpc` — RPC endpoint for Ethereum network.
- `--safe-address` — Safe contract address.
- `--to` — Target contract address.
- `--value` — Amount in wei.
- `--data` — Calldata (hex).
- `--safe-nonce` — Safe contract nonce.
- `--gas-token` — Gas token address (optional).
- `--refund-receiver` — Address to receive gas refunds (optional).
- `--output-json` — Path to save EIP-712 JSON.

If arguments are omitted, the CLI will prompt for them interactively. All steps can be automated for CI/CD or scripting.

**Example:**

```bash
mox msig tx-build --url http://localhost:8545 --safe-address 0xSafe... --to 0xTarget... --operation 0 --value 0 --data 0x...
```

Or run interactively:

```bash
mox msig tx-build
```

### `mox msig tx-sign`

Sign a Safe multisig transaction from EIP-712 JSON, with strict domain validation and owner checks.

**Arguments:**

- `--url` or `--rpc` — RPC endpoint for Ethereum network.
- `--input-json` — Path to EIP-712 SafeTx JSON to sign. If omitted, prompts interactively.
- `--output-json` — Path to output signed SafeTx JSON (can overwrite input). If omitted, prompts interactively.
- `--account` — Account name (from keystore) to sign with.
- `--private-key` — Private key to sign with.
- `--password` — Password for keystore account (can be prompted).
- `--password-file-path` — Path to file containing password for keystore account.

**Prompts:**

- If not provided, prompts for signer (account name or private key).
- Prompts for password if using keystore account.
- Prompts for confirmation before signing.
- Displays SafeTx details and enforces owner/domain checks.

**Example:**

```bash
mox msig tx-sign --url http://localhost:8545 --input-json ./safe_tx.json --output-json ./safe_tx_signed.json --account mykeystore
```

Or run interactively:

```bash
mox msig tx-sign
```

### `mox msig tx-broadcast`

Broadcast a signed Safe multisig transaction to the blockchain.

**Arguments:**

- `--url` or `--rpc` — RPC endpoint for Ethereum network.
- `--input-json` — Path to EIP-712 SafeTx JSON to broadcast. If omitted, prompts interactively.
- `--output-json` — Path to output broadcasted SafeTx JSON (can overwrite input). If omitted, prompts interactively.
- `--account` — Account name (from keystore) to broadcast with.
- `--private-key` — Private key to broadcast with.
- `--password` — Password for keystore account (can be prompted).
- `--password-file-path` — Path to file containing password for keystore account.

**Prompts & Validation:**

- Prompts for broadcaster (account name or private key) if not provided.
- Prompts for password if using keystore account.
- Validates SafeTx has not already been broadcasted and has enough signers (threshold check).
- Checks Safe contract balance and funds for gas before broadcasting.
- Displays estimated cost in wei and SafeTx details before broadcasting.
- Interactive confirmation before broadcasting, with display of transaction hash and broadcasted transaction details.

**Example:**

```bash
mox msig tx-broadcast --url http://localhost:8545 --input-json ./safe_tx_signed.json --output-json ./safe_tx_broadcasted.json --account mykeystore
```

Or run interactively:

```bash
mox msig tx-broadcast
```

## Interactive Usage & Fallbacks

- If any required argument is omitted, the CLI will prompt for it interactively.
- For signing and broadcasting, if `--input-json` or `--output-json` is omitted, you will be prompted for the file path.
- For keystore accounts, you will be prompted for the account name and password if not provided.
- All prompts are branded and support history/autosuggest for convenience.

## Local Development & Testing

### Run Anvil and Deploy Safe Contract

> Ensure you use `uv run` or activate your venv

Start Anvil:

```bash
anvil
```

Deploy Safe and MultiSend contracts for local testing:

```bash
python moccasin/msig_cli/scripts/deploy_local_safe.py
```

This sets environment variables for Safe and MultiSend addresses for your CLI/test runs.

### Running Tests Locally

Tests run locally on Anvil. Make sure Anvil is running and contracts are deployed:

```bash
just test-msig
```

Tests use static JSON and local contract addresses for reproducibility.

<details>
  <summary>Example:</summary>

```json
{
  "safeTx": {
    "types": {
      "EIP712Domain": [
        {
          "name": "chainId",
          "type": "uint256"
        },
        {
          "name": "verifyingContract",
          "type": "address"
        }
      ],
      "SafeTx": [
        {
          "name": "to",
          "type": "address"
        },
        {
          "name": "value",
          "type": "uint256"
        },
        {
          "name": "data",
          "type": "bytes"
        },
        {
          "name": "operation",
          "type": "uint8"
        },
        {
          "name": "safeTxGas",
          "type": "uint256"
        },
        {
          "name": "baseGas",
          "type": "uint256"
        },
        {
          "name": "gasPrice",
          "type": "uint256"
        },
        {
          "name": "gasToken",
          "type": "address"
        },
        {
          "name": "refundReceiver",
          "type": "address"
        },
        {
          "name": "nonce",
          "type": "uint256"
        }
      ]
    },
    "primaryType": "SafeTx",
    "domain": {
      "verifyingContract": "0x5FbDB2315678afecb367f032d93F642f64180aa3",
      "chainId": 31337
    },
    "message": {
      "to": "0x0000000000000000000000000000000000000000",
      "value": 0,
      "data": "0xa9059cbb00000000000000000000000070997970c51812dc3a010c7d01b50e0d17dc79c8000000000000000000000000000000000000000000000000000000000000002a",
      "operation": 0,
      "safeTxGas": 0,
      "baseGas": 0,
      "dataGas": 0,
      "gasPrice": 0,
      "gasToken": "0x0000000000000000000000000000000000000000",
      "refundReceiver": "0x0000000000000000000000000000000000000000",
      "nonce": 0
    }
  },
  "signatures": "0x75803cc9d95c2acf329e1a9eaf998b1148616953dc2a45631962a903f243b88f095b282dc1ea266203769931bd14a1a477709623e33f9950ff3bb2a9a1c73ffb1b"
}
```

</details>

> **Note:** Broadcast needs the two previous steps to be run first to ensure Safe tx data is correctly encoded.

### About SafeTxGas and BaseGas

SafeTxGas and BaseGas are critical parameters for Safe multisig transactions:

- **SafeTxGas** is the gas allocated for executing the internal transaction(s) within the Safe contract. For batch transactions (MultiSend), a sensible default is `200,000`.
- **BaseGas** covers the overhead of signature verification and Safe contract logic. The minimum is `21,000`, which is the cost of a simple ETH transfer.

If these values are set too low, the Safe contract will revert with an error (e.g., `GS010: Not enough gas to execute safe transaction`).

**Best Practice:**

- For MultiSend batches, set `safeTxGas=200000` and `baseGas=21000` as defaults. Increase if you have many internal transactions or complex logic.
- For single transactions, gas estimation is performed automatically.

**References:**

- [Gnosis Safe Error Codes](https://github.com/safe-global/safe-contracts/blob/main/docs/error_codes.md)

---

## Project Structure

- `msig.py` — Main CLI logic and workflow
- `tx/tx_build.py` — Transaction builder
- `tx/tx_sign.py` — Transaction signer
- `tx/build_prompts.py`, `tx/sign_prompts.py`, `tx/broadcast_prompts.py` ,`common_prompts.py` — Modular, branded prompts
- `tx/tx_broadcast.py` — Transaction broadcaster
- `utils/` — Helpers, types, exceptions, validation
- `scripts/deploy_local_safe.py` — Local deployment for testing

---

## Developer Checklist / TODO

- [x] Build and sign commands with robust validation and error handling
- [x] Local deployment and test support (Anvil)
- [x] Implement `tx_broadcast` for transaction execution
- [x] Add unit and integration tests for new features
- [x] Add more owners and a threshold while deploying locally
- [x] Display SafeTx internal transactions in pretty_print
- [x] Add support for gas token estimation
- [x] Add support for raw data internal transactions
- [ ] Improve function parameter type handling (arrays, bytes, etc.)
- [ ] Improve test suite and add more scenarios
- [ ] Add proper typing to prompts and functions
- [ ] Consider addin a new wokflow from encoded SafeTx msg and domains rathen than JSON
- [ ] Prompt metamask when we init account, sign and broadcast
- [ ] Consider grouping all tx-related commands under `mox msig tx` with flags for build, sign, broadcast
- [ ] Consider adding `sign` to sign simple messages in the future
- [ ] See if we can convert all process with boa rather than w3 (maybe run it on pyevm)

# Troubleshooting

> `ERROR: Error running msig command: not well-formed (invalid token): line 1, column 222`

This error comes from the anvil not running and also the deployment script not being run. Make sure to run the deployment script first:

```bash
# In a separate terminal, start Anvil
anvil
# Then run the deployment script
python moccasin/msig_cli/scripts/deploy_local_safe.py
```

Or if you have `just` installed, you can run:

```bash
just deploy-safe
```

Note: if you run `msig tx_sign` against a JSON file that has not been updated with the correct `verifyingAddress`, you will get an EVM error like:

```bash
Unexpected error during transaction build: ('execution reverted', '0x')
```

To avoid this, ensure the `verifyingAddress` in your JSON matches the Safe contract address deployed by the script.

```bash
➜ python moccasin/msig_cli/scripts/deploy_local_safe.py
Safe deployed successfully: 0x559da2BFD9e8F7D2fa3C6F851f2aE962Cc06aD42
MultiSend deployed successfully: 0xCf7Ed3AccA5a467e9e704C703E8D87F634fB0Fc9
```

> `Error broadcasting SafeTx with account 0x...: Execution reverted: GS026`

```

The error `execution reverted: GS026` means "Invalid owner provided" in Gnosis Safe contracts.

Why is this happening? The Safe contract checks that all signatures are from valid owners. If any signature is from an address not in the Safe's owner list, the transaction is rejected with GS026.

But it's possible that the transaction data is wrong and the owner list is set correctly. This can happen if:
- The Safe contract address is incorrect.
- The Safe nonce is not correctly set.
- The transaction data (to, value, data) is malformed or does not match the expected format.

To fix this, ensure:
1. The Safe contract address is correct and matches the one deployed by the script.
2. The Safe nonce is set correctly and matches the current nonce of the Safe.
3. The transaction data (to, value, data) is valid and matches the expected format

```

---

See [`msig.py`](../commands/msig.py) and [`msig_cli`](.) for full implementation details.
See [`tx_build.py`](tx/tx_build.py), [`tx_sign.py`](tx/tx_sign.py), [`tx_broadcast.py`](tx/tx_broadcast.py) for transaction builder and signer logic.
See [`scripts/deploy_local_safe.py`](scripts/deploy_local_safe.py) for local deployment.
