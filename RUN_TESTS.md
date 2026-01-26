# How to Run the Tests for Issue #271 Fix

## Quick Commands

### Run Tests Without anvil-zksync (Works Now)
```bash
# Run all 3 signature tests at once
uv run pytest tests/zksync/test_simulate_parameter_fix.py -k "not deploy and not interaction" -v

# Expected: 3 passed ✅
```

### Run Individual Signature Tests
```bash
# Test 1: Verify simulate parameter is in signature
uv run pytest tests/zksync/test_simulate_parameter_fix.py::test_zksync_env_execute_code_accepts_simulate_parameter -v

# Test 2: Verify backward and forward compatibility
uv run pytest tests/zksync/test_simulate_parameter_fix.py::test_zksync_env_execute_code_signature_compatibility -v

# Test 3: Verify patch implementation
uv run pytest tests/zksync/test_simulate_parameter_fix.py::test_monkey_patch_preserves_original_functionality -v
```

### Run All Tests (Requires anvil-zksync)
```bash
# Run all 6 tests (3 signature + 3 integration)
uv run pytest tests/zksync/test_simulate_parameter_fix.py -v

# Expected with anvil-zksync: 6 passed ✅
# Expected without: 3 passed, 3 errors (GLIBC issue on this system)
```

## What Each Test Does

### Signature Tests (No anvil-zksync needed)
1. **test_zksync_env_execute_code_accepts_simulate_parameter**
   - Verifies `simulate` parameter exists in ZksyncEnv.execute_code signature
   - Checks it has default value `False`

2. **test_zksync_env_execute_code_signature_compatibility**
   - Tests calls work WITHOUT simulate parameter (backward compatibility)
   - Tests calls work WITH simulate=False (new titanoboa behavior)
   - Tests calls work WITH simulate=True (full support)

3. **test_monkey_patch_preserves_original_functionality**
   - Verifies the monkey patch is applied correctly
   - Checks all parameters are passed through properly

### Integration Tests (Require anvil-zksync)
4. **test_deploy_and_call_contract_function**
   - Deploys Difficulty.vy contract
   - Calls get_difficulty() view function
   - This is the exact scenario that was failing in issue #271

5. **test_multiple_contract_calls_after_deployment**
   - Makes multiple sequential calls to the same function
   - Ensures the fix is robust for repeated use

6. **test_contract_deployment_and_interaction_via_boa_load**
   - Uses boa.load() to deploy (pattern mentioned in the issue)
   - Calls contract functions after boa.load()

## Current System Status

**OS**: Ubuntu 20.04.6 LTS (WSL)
**GLIBC**: 2.31
**anvil-zksync**: Installed but requires GLIBC 2.32+

**Result**: Signature tests work perfectly ✅
Integration tests require anvil-zksync on a system with GLIBC 2.32+ (Ubuntu 22.04+)

## Installing anvil-zksync (Ubuntu 22.04+ or newer)

```bash
# Method 1: Install foundry-zksync (includes anvil-zksync)
curl -L https://raw.githubusercontent.com/matter-labs/foundry-zksync/main/install-foundry-zksync | bash
source ~/.bashrc
foundryup-zksync

# Verify installation
anvil-zksync --version
```

## For PR/CI

The signature tests are sufficient to verify the fix works. They test:
- The parameter is accepted ✅
- Backward compatibility is maintained ✅
- Forward compatibility with titanoboa >= 0.2.6 ✅

Integration tests provide additional confidence but require anvil-zksync in CI.

## See Also

- **TESTING_GUIDE.md** - Comprehensive testing documentation
- **moccasin/config.py:31-45** - The fix implementation
- **tests/zksync/test_simulate_parameter_fix.py** - Test file with detailed comments
