# 0.3.3 

## Enhancements

## Bug Fixes

## Breaking 
- `unsafe_password_file` will no longer be in `networks.NETWORK_NAME`, but will be moved to `networks.NETWORK_NAME.ACCOUNTS`, like so:

From

```toml 
[networks.anvil]
unsafe_password_file = "$ANVIL1_PASSWORD_FILE"
default_account_name = "anvil1"
```

TO

```toml 
[networks.anvil]
default_account_name = "anvil1"

[[networks.anvil.accounts]]
name = "anvil1"
unsafe_password_file = "$ANVIL1_PASSWORD_FILE"
```