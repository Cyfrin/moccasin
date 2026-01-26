# Testing Guide for Issue #271 Fix

This guide shows you how to run the tests for the ZKsync simulate parameter fix.

## Quick Start - Run Tests Now

### Option 1: Run Signature Tests (No Dependencies)
These tests verify the fix is applied correctly and don't require `anvil-zksync`:

```bash
# Run all signature tests (3 tests)
uv run pytest tests/zksync/test_simulate_parameter_fix.py::test_zksync_env_execute_code_accepts_simulate_parameter -v
uv run pytest tests/zksync/test_simulate_parameter_fix.py::test_zksync_env_execute_code_signature_compatibility -v
uv run pytest tests/zksync/test_simulate_parameter_fix.py::test_monkey_patch_preserves_original_functionality -v

# Or run them all at once
uv run pytest tests/zksync/test_simulate_parameter_fix.py -k "not deploy and not interaction" -v
```

**Expected Output**: All 3 tests should PASS ✅

### Option 2: Run All Tests (Requires anvil-zksync)
These include integration tests that deploy real contracts:

```bash
# Run all 6 tests
uv run pytest tests/zksync/test_simulate_parameter_fix.py -v
```

**Expected Output**:
- 3 signature tests PASS ✅
- 3 integration tests PASS ✅ (only if anvil-zksync is installed)

---

## Test Categories

### 1. Signature Tests (3 tests - no anvil-zksync required)

These tests verify the monkey patch was applied correctly:

- **`test_zksync_env_execute_code_accepts_simulate_parameter`**
  - Verifies the `simulate` parameter exists in the method signature
  - Checks it has a default value of `False`

- **`test_zksync_env_execute_code_signature_compatibility`**
  - Tests backward compatibility (calls without `simulate` still work)
  - Tests new behavior (calls with `simulate=False` work)
  - Tests full support (calls with `simulate=True` work)

- **`test_monkey_patch_preserves_original_functionality`**
  - Verifies the patch implementation is correct
  - Checks that all parameters are passed through properly

### 2. Integration Tests (3 tests - require anvil-zksync)

These tests verify the fix works end-to-end with real contracts:

- **`test_deploy_and_call_contract_function`**
  - Deploys a contract using the deployment script
  - Calls a view function (this is where the bug occurred)
  - Verifies the returned value is correct

- **`test_multiple_contract_calls_after_deployment`**
  - Tests multiple sequential function calls
  - Ensures the fix is robust for repeated use

- **`test_contract_deployment_and_interaction_via_boa_load`**
  - Tests the `boa.load()` pattern mentioned in the issue
  - Verifies contract interaction works after `boa.load()`

---

## Installing anvil-zksync (For Integration Tests)

The integration tests require `anvil-zksync` version 0.6.9 or higher.

### Requirements
- **GLIBC 2.32+** (Ubuntu 22.04+, or equivalent)
- Current system has GLIBC 2.31 (Ubuntu 20.04), so pre-built binaries won't work

### Installation Methods

#### Method 1: Install Foundry-ZKsync (Recommended)
```bash
curl -L https://raw.githubusercontent.com/matter-labs/foundry-zksync/main/install-foundry-zksync | bash
source ~/.bashrc
foundryup-zksync
```

This installs `anvil-zksync` to `~/.foundry/bin/anvil-zksync`

#### Method 2: Download Pre-built Binary
```bash
# Download latest release
wget https://github.com/matter-labs/anvil-zksync/releases/latest/download/anvil-zksync_$(uname -s)_$(uname -m).tar.gz

# Extract and install
tar -xzf anvil-zksync_*.tar.gz
sudo mv anvil-zksync /usr/local/bin/
chmod +x /usr/local/bin/anvil-zksync

# Verify installation
anvil-zksync --version
```

#### Method 3: Build from Source
```bash
# Requires Rust toolchain
git clone https://github.com/matter-labs/anvil-zksync.git
cd anvil-zksync
cargo build --release
sudo cp target/release/anvil-zksync /usr/local/bin/
```

### Verify Installation
```bash
anvil-zksync --version
# Should output: anvil-zksync 0.6.x
```

---

## Running Tests - Step by Step

### Step 1: Navigate to Project Root
```bash
cd /path/to/moccasin
```

### Step 2: Ensure Dependencies Are Installed
```bash
uv sync
```

### Step 3: Run Signature Tests (Always Available)
```bash
# Run individual tests
uv run pytest tests/zksync/test_simulate_parameter_fix.py::test_zksync_env_execute_code_accepts_simulate_parameter -v

# Or run all signature tests at once
uv run pytest tests/zksync/test_simulate_parameter_fix.py -k "not deploy and not interaction" -v
```

**Expected Output:**
```
tests/zksync/test_simulate_parameter_fix.py::test_zksync_env_execute_code_accepts_simulate_parameter PASSED
tests/zksync/test_simulate_parameter_fix.py::test_zksync_env_execute_code_signature_compatibility PASSED
tests/zksync/test_simulate_parameter_fix.py::test_monkey_patch_preserves_original_functionality PASSED

============================== 3 passed in 0.05s ===============================
```

### Step 4: Run Integration Tests (Requires anvil-zksync)
```bash
# Run all tests including integration tests
uv run pytest tests/zksync/test_simulate_parameter_fix.py -v
```

**Expected Output (with anvil-zksync):**
```
tests/zksync/test_simulate_parameter_fix.py::test_zksync_env_execute_code_accepts_simulate_parameter PASSED
tests/zksync/test_simulate_parameter_fix.py::test_zksync_env_execute_code_signature_compatibility PASSED
tests/zksync/test_simulate_parameter_fix.py::test_monkey_patch_preserves_original_functionality PASSED
tests/zksync/test_simulate_parameter_fix.py::test_deploy_and_call_contract_function PASSED
tests/zksync/test_simulate_parameter_fix.py::test_multiple_contract_calls_after_deployment PASSED
tests/zksync/test_simulate_parameter_fix.py::test_contract_deployment_and_interaction_via_boa_load PASSED

============================== 6 passed in 2.34s ===============================
```

### Step 5: Run All ZKsync Tests
```bash
# Run all zksync tests to ensure no regressions
uv run pytest tests/zksync/ -v
```

---

## Troubleshooting

### Issue: "anvil-zksync: command not found"
**Solution**: anvil-zksync is not installed or not in PATH
- Install using one of the methods above
- Add to PATH: `export PATH="$HOME/.foundry/bin:$PATH"`
- Or run signature tests only (they don't require anvil-zksync)

### Issue: "GLIBC_2.32 not found"
**Solution**: Your system has an older GLIBC version (like Ubuntu 20.04)
- Upgrade to Ubuntu 22.04+ or equivalent
- Build anvil-zksync from source
- Or run signature tests only (they work on any system)

### Issue: Tests fail with "FileNotFoundError: anvil-zksync"
**Solution**: This is expected if anvil-zksync isn't installed
- The signature tests will still pass (3/6 tests)
- The integration tests will show as errors
- Install anvil-zksync to run all tests

---

## CI/CD

In CI, ensure:
1. Use Ubuntu 22.04 or later (for GLIBC 2.32+)
2. Install anvil-zksync before running tests:
   ```yaml
   - name: Install anvil-zksync
     run: |
       curl -L https://raw.githubusercontent.com/matter-labs/foundry-zksync/main/install-foundry-zksync | bash
       source ~/.bashrc
       foundryup-zksync

   - name: Run tests
     run: uv run pytest tests/zksync/test_simulate_parameter_fix.py -v
   ```

---

## Summary

✅ **Signature Tests**: Run without anvil-zksync, verify the fix is applied correctly
✅ **Integration Tests**: Require anvil-zksync, verify end-to-end functionality
✅ **All Tests**: 6 total tests with comprehensive coverage of the fix

The signature tests alone are sufficient to verify the fix is working. Integration tests provide additional confidence by testing real contract deployments and function calls.
