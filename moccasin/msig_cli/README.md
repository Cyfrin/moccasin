# Moccasin Multisig CLI

This module provides a command-line interface for building, signing, and broadcasting Safe multisig transactions and messages. It is designed for both interactive use and automation, making it suitable for offline developer workflows.

## Features

- **Interactive Transaction Builder:**
  - Build Safe multisig transactions with prompts for all required fields.
  - Supports both single transactions and batch (MultiSend) operations.
- **Input Validation:**
  - Validates addresses, calldata, and other parameters.
  - Can use defaults or scripted values if arguments are omitted.
- **Batch Operations:**
  - MultiSend support for batching multiple internal transactions.
- **EIP-712 Structured Data Output:**
  - Optionally outputs EIP-712 JSON for signing and verification.
- **Extensible CLI:**
  - Designed for future commands (sign, broadcast, etc.) and integration with external tools.

## CLI Commands

### `mox msig tx_build`

Build a Safe multisig transaction interactively or via command-line arguments.

**Arguments:**

- `--rpc-url` — RPC endpoint for Ethereum network.
- `--safe-address` — Safe contract address.
- `--to` — Target contract address.
- `--operation` — Operation type (`0` for call, `1` for delegate call).
- `--value` — Amount in wei.
- `--data` — Calldata (hex).
- `--safe-nonce` — Safe contract nonce.
- `--gas-token` — Gas token address (optional).
- `--json-output` — Path to save EIP-712 JSON.

If arguments are omitted, the CLI will prompt for them interactively. All steps can be automated for CI/CD or scripting.

**Example:**

```bash
mox msig tx_build --rpc-url http://localhost:8545 --safe-address 0xSafe... --to 0xTarget... --operation 0 --value 0 --data 0x...
```

Or run interactively:

```bash
mox msig tx_build
```

### `mox msig tx_sign`

Sign a Safe multisig transaction from EIP-712 JSON, with strict domain validation and owner checks.

**Arguments:**

- `--rpc-url` — RPC endpoint for Ethereum network.
- `--signer` — Account name (from keystore) or private key to sign with.
- `--input-json` — Path to EIP-712 SafeTx JSON to sign.
- `--output-json` — Path to output signed SafeTx JSON (can overwrite input).

**Prompts:**

- If not provided, prompts for signer (account name or private key).
- Prompts for password if using keystore account.
- Prompts for confirmation before signing.
- Displays SafeTx details and enforces owner/domain checks.

**Example:**

```bash
mox msig tx_sign --rpc-url http://localhost:8545 --signer anvil0 --input-json ./safe_tx.json --output-json ./safe_tx.json
```

Or run interactively:

```bash
mox msig tx_sign
```

---

## Local Development & Testing

### Run Anvil and Deploy Safe Contract (WIP: add owners/threshold)

> Ensure you use `uv run` or activate you venv

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
pytest tests/cli/test_cli_msig.py -vvv
```

Tests use static JSON and local contract addresses for reproducibility.

**Example:**

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

---

## Project Structure

- `msig_cli.py` — Main CLI logic and workflow
- `tx/tx_build.py` — Transaction builder
- `tx/tx_sign.py` — Transaction signer
- `tx/build_prompts.py`, `tx/sign_prompts.py`, `common_prompts.py` — Modular, branded prompts
- `utils/` — Helpers, types, exceptions, validation
- `scripts/deploy_local_safe.py` — Local deployment for testing

---

## Developer Checklist / TODO

- [x] Build and sign commands with robust validation and error handling
- [x] Local deployment and test support (Anvil)
- [ ] Implement `tx_execute` for transaction execution
- [ ] Add support for ERC20 transfers and raw data internal transactions
- [ ] Improve function parameter type handling (arrays, bytes, etc.)
- [ ] Add message signing (`msg` subcommand)
- [ ] Extend validation for more Ethereum types
- [ ] Add unit and integration tests for new features
- [ ] Add more owners and a threshold while deploying locally

---

See [`tx_build.py`](tx/tx_build.py) and [`tx_sign.py`](tx/tx_sign.py) for transaction builder and signer logic.
See [`scripts/deploy_local_safe.py`](scripts/deploy_local_safe.py) for local deployment.
