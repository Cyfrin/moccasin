>[!IMPORTANT]
> *This repo is a work in progress and is not ready for production use.*

# Moccasin

A fast, pythonic, Vyper smart contract testing and development framework.

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

<!-- <p align="center">
    <br />
    <a href="https://cyfrin.io/">
        <img src="./img/moccasin-logo.png" width="250" alt=""/></a>
    <br />
</p> -->

Fast to install, test, and run python commands on your smart contracts.

# Quickstart

Head over to [the moccasin installation documentation](https://cyfrin.github.io/moccasin/installing-moccasin.html) to for other install methodologies and getting stated.

## This README Quickstart

To install the moccasin `mox` command, we recommend the [uv](https://docs.astral.sh/uv/) tool.

```bash
uv tool install moccasin
```

Then, see a list of commands with:

```bash
mox --help
```

# Documentation

The documentation roughly attempts to follow [Diátaxis](https://diataxis.fr/).

# Speed Comparisons

*The following comparisions were done taking the `user` result from running the bash `time` command followed by the appropriote command on an M3 MacOS*
*Compile command tested with a basic vyper counter contract on version 0.4.0 or 0.3.10 depending on compatibility*


| Command | Moccasin | Brownie | Hardhat | Foundry | Ape   |
| ------- | -------- | ------- | ------- | ------- | ----- |
| help    | 0.03s    | 0.37s   | 0.30s   | 0.01s   | 2.55s |
| init    | 0.04s    | 0.37s   | xx      | 0.20s   | 5.08s |
| compile | 0.49s    | 0.42s   | xx      | 0.17s   | 2.00s |


# Acknowledgements 

- [brownie](https://github.com/eth-brownie/brownie)
- [vyper](https://github.com/vyperlang/vyper)
- [boa](https://github.com/vyperlang/titanoboa)

## Background

> Agkistrodon piscivorus is a species of venomous snake, a pit viper in the subfamily Crotalinae of the family Viperidae. The generic name is derived from the Greek words ἄγκιστρον agkistron "fish-hook, hook" and ὀδών odon "tooth", and the specific name comes from the Latin piscis 'fish' and voro '(I) eat greedily, devour'; thus, the scientific name translates to "hook-toothed fish-eater". Common names include cottonmouth, northern cottonmouth, water moccasin, swamp moccasin, black moccasin, and simply viper.