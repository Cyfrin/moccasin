>[!IMPORTANT]
> *This repo is a work in progress and is not ready for production use.*

# Gaboon

A fast, pythonic, Vyper smart contract testing and development framework.

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

<p align="center">
    <br />
    <a href="https://cyfrin.io/">
        <img src="./img/gaboon-logo.png" width="250" alt=""/></a>
    <br />
</p>

Fast to install, test, and run python commands on your smart contracts.

# Speed Comparisons

*The following comparisions were done taking the `user` result from running the bash `time` command followed by the appropriote command on an M3 MacOS*
*Compile command tested with a basic vyper counter contract on version 0.4.0 or 0.3.10 depending on compatibility*


| Command | Gaboon | Brownie | Hardhat | Foundry | Ape   |
| ------- | ------ | ------- | ------- | ------- | ----- |
| help    | 0.03s  | 0.37s   | 0.30s   | 0.01s   | 2.55s |
| init    | 0.04s  | 0.37s   | xx      | 0.20s   | 5.08s |
| compile | 0.49s  | 0.42s   | xx      | 0.17s   | 2.00s |


# Acknowledgements 

- [brownie](https://github.com/eth-brownie/brownie)
- [vyper](https://github.com/vyperlang/vyper)
- [boa](https://github.com/vyperlang/titanoboa)

## Background

> The Gaboon viper (Bitis gabonica), also called the Gaboon adder, is a viper species found in the rainforests and savannas of sub-Saharan Africa. Like all other vipers, it is venomous. It is the largest member of the genus Bitis, and has the longest fangs of any venomous snake – up to 2 inches (5 cm) in length – and the highest venom yield of any snake. No subspecies are recognized.