>[!IMPORTANT]
> *This repo is a work in progress and is not ready for production use.*

# Gaboon

A fast, pythonic, Vyper smart contract testing and development framework.

[![Rye](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/rye/main/artwork/badge.json)](https://rye.astral.sh)


## MVP requirements

- [x] Initialize a project (`gab init`)
- [x] Compile vyper projects (`gab compile`/`gab build`)
- [x] Deploy vyper projects (`gab run <script>`)
  - [x] Deploy locally (boa VM)
  - [x] Deploy to a testnet
  - [x] Deploy to a mainnet
  - [x] Deploy to a forked network
- [x] Test vyper projects (`gab test`)
- [x] Import/generate keystores (`gab wallet import`)
- [x] `gab install (<github_repo>)`
- [ ] Patrick to add like `EVMToZKSync` API.

Should be fast to install and test. 

Commands for MVP:
```bash
init ✅
compile ✅
wallet ✅
run ✅ 
test ✅
install ✅
```

## Background

The Gaboon viper (Bitis gabonica), also called the Gaboon adder, is a viper species found in the rainforests and savannas of sub-Saharan Africa.[1][3][2] Like all other vipers, it is venomous. It is the largest member of the genus Bitis,[4][5] and has the longest fangs of any venomous snake – up to 2 inches (5 cm) in length – and the highest venom yield of any snake.[5][6] No subspecies are recognized.[3][7]


## Later

- [ ] halmos built-in
- [ ] Manage networks `gab networks <add|remove|list>`
- [ ] [rust/python/pyo3 modules for more performance](https://www.maturin.rs/tutorial)
- [ ] fuzzing 
- [ ] `gab console`
- [ ] ENS Support
- [ ] Password files in the `gaboon.toml` for decrypting accounts
- [ ] solidity support
- [ ] medusa fuzzer
- [ ] mojo support
- [ ] Track deployments
  - [ ] Be able to do like `from gaboon import deployments\n deployments[0]`

# Speed Comparisons

*The following comparisions were done taking the `real` result from running the bash `time` command followed by the appropriote command*

| Command | Gaboon   | Brownie  | Hardhat  | Foundry  | Ape      |
| ------- | -------- | -------- | -------- | -------- | -------- |
| help    | 0m0.129s | 0m1.863s | 0m1.335s | 0m0.032s | 0m3.407s |
| init    | 0m0.136s | 0m1.169s | xx       | 0m0.922s | 0m4.937s |


# Acknowledgements 

- [brownie](https://github.com/eth-brownie/brownie)
- [vyper](https://github.com/vyperlang/vyper)
- [boa](https://github.com/vyperlang/titanoboa)

# Gaboon Viper

> The Gaboon viper (Bitis gabonica), also called the Gaboon adder, is a viper species found in the rainforests and savannas of sub-Saharan Africa. Like all other vipers, it is venomous. It is the largest member of the genus Bitis, and has the longest fangs of any venomous snake – up to 2 inches (5 cm) in length – and the highest venom yield of any snake. No subspecies are recognized.
