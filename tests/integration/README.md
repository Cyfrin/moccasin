There are tests where you need some kind of environment variable or external service. For example:

- Etherscan
- GitHub

# Requirements

To run this folder, you'll need:

1. `EXPLORER_API_KEY` set to an Etherscan API key
2. `OPTIMISTIC_ETHERSCAN_API_KEY` set to an Etherscan-Optimism API key
3. `MAINNET_RPC_URL` set to your mainnet RPC URL from your provider (like [Alchemy](https://www.alchemy.com/))

> 💡 You'll have to export your env variables before running `just test-i`.
>
> You can create a script to export them whenever you need them.
> For extra security, check this password management tool [pass](https://www.passwordstore.org/) to encrypt your var with `gpg`.
>
> Ask any contributor if you need advice.