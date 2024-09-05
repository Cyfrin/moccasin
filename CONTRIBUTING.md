# Contributing

Thank you for wanting to contribute! This project reviews PRs that have an associated issue with 
them. If you have not make an issue for your PR, please make one first. 

Issues, feedback, and sharing that you're using Titanoboa and Vyper on social media is always welcome!

# Table of Contents

- [Contributing](#contributing)
- [Table of Contents](#table-of-contents)
- [Setup](#setup)
  - [Requirements](#requirements)
  - [Installing for local development](#installing-for-local-development)
  - [Running Tests](#running-tests)
- [Code Style Guide](#code-style-guide)
- [Thank you!](#thank-you)

# Setup

## Requirements

You must have the following installed to proceed with contributing to this project. 

- [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
  - You'll know you did it right if you can run `git --version` and you see a response like `git version x.x.x`
- [python](https://www.python.org/downloads/)
  - You'll know you did it right if you can run `python --version` and you see a response like `Python x.x.x`
- [rye](https://rye.astral.sh)
  - You'll know you did it right if you can run `rye --version` and you see a response like `rye 0.36.0 \n commit: 0.36.0 (12c024c7c 2024-07-07)...`
- [anvil](https://book.getfoundry.sh/reference/anvil/)
  - You'll know you did it right if you can run `anvil --version` and you see a response like `anvil 0.2.0 (b1f4684 2024-05-24T00:20:06.635557000Z)`
- Linux and/or MacOS
  - This project is not tested on Windows, so it is recommended to use a Linux or MacOS machine, or use a tool like [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) for windows users.

## Installing for local development 

Follow the steps to clone the repo for you to make changes to this project.

1. Clone the repo

```bash
git clone https://github.com/vyperlang/gaboon
cd gaboon
```

2. Sync dependencies

*This repo uses rye to manage python dependencies and version. So you don't have to deal with virtual environments (much)*

```bash
rye sync
```

*Note: When you delete your terminal/shell, you will need to reactivate this virtual environment again each time. To exit this python virtual environment, type `deactivate`*

3. Create a new branch

```bash
git checkout -b <branch_name>
```

And start making your changes! Once you're done, you can commit your changes and push them to your forked repo.

```bash
git add .
git commit -m 'your commit message'
git push <your_forked_github>
```

## Running Tests

First, you'll need to make sure you have the `anvil1` keystore in your `~/.gaboon/keystores` folder. You can [find it here](./tests/data/keystores/anvil1). Please move it there. 

Run the following:

```bash
rye run test
```
This is equivalent to running `pytest` in the root directory of the project (see the `pyproject.toml` under `[tool.rye.scripts]` for what this `test` command does).

# Code Style Guide

We will run the `.github/workflows` before merging your PR to ensure that your code is up to standard. Be sure to run the scripts in there before submitting a PR.

For type checking:

```bash
rye run typecheck
```

For code formatting: 

```bash
rye run format
```

## Where do you get the `typecheck` and `format` command?

You can see in `pyproject.toml` under the `tool.rye.scripts` section a list of scripts one can run with `rye run X`.

# Thank you!

Thank you for wanting to participate in titanoboa and gaboon!