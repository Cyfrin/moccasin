
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

### Example

```bash
mox msig tx_build --rpc-url https://rpc-url --safe-address 0xSafe... --to 0xTarget... --operation 0 --value 0 --data 0x...
```

Or run interactively:

```bash
mox msig tx_build
```

## Developer Checklist / TODO

- [ ] Implement `tx_sign` command for signing transactions.
- [ ] Implement `tx_broadcast` command for broadcasting signed transactions.
- [ ] Add support for ERC20 transfer and raw data internal transaction types.
- [ ] Improve function parameter type handling (arrays, bytes, etc.).
- [ ] Add message signing (`msg` subcommand).
- [ ] Extend validation for more Ethereum types.
- [ ] Add unit and integration tests for new features.

---

See [`tx_build.py`](tx/tx_build.py) for transaction builder logic.
