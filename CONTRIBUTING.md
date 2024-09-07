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
  - [Where do you get the `typecheck` and `format` command?](#where-do-you-get-the-typecheck-and-format-command)
- [Thank you!](#thank-you)

# Setup

## Requirements

You must have the following installed to proceed with contributing to this project. 

- [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
  - You'll know you did it right if you can run `git --version` and you see a response like `git version x.x.x`
- [python](https://www.python.org/downloads/)
  - You'll know you did it right if you can run `python --version` and you see a response like `Python x.x.x`
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
  - You'll know you did it right if you can run `uv --version` and you see a response like `uv 0.4.7 (a178051e8 2024-09-07)`
- [anvil](https://book.getfoundry.sh/reference/anvil/)
  - You'll know you did it right if you can run `anvil --version` and you see a response like `anvil 0.2.0 (b1f4684 2024-05-24T00:20:06.635557000Z)`
- Linux and/or MacOS
  - This project is not tested on Windows, so it is recommended to use a Linux or MacOS machine, or use a tool like [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) for windows users.
- [just](https://github.com/casey/just)
  - You'll know you did it right if you can run `just --version` and you see a response like `just 1.35.0`

## Installing for local development 

Follow the steps to clone the repo for you to make changes to this project.

1. Clone the repo

```bash
git clone https://github.com/vyperlang/gaboon
cd gaboon
```

2. Sync dependencies

*This repo uses uv to manage python dependencies and version. So you don't have to deal with virtual environments (much)*

```bash
uv sync
```

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

4. Virtual Environment

You can then (optionally) work with the virtual environment created by `uv`.

```bash
source .venv/bin/activate
```

And to remove the virtual environment, just run:
```bash
deactivate
```

However, if you run tests and scripts using the `uv` or `just` commands as we will describe below, you won't have to worry about that. 

*Note: When you delete your terminal/shell, you will need to reactivate this virtual environment again each time. To exit this python virtual environment, type `deactivate`*

## Running Tests

First, you'll need to make sure you have the `anvil1` keystore in your `~/.gaboon/keystores` folder. You can [find it here](./tests/data/keystores/anvil1). Please move it there. 

Run the following:

```bash
just test # Check out the justfile to see the command this runs
```
This is equivalent to running `pytest` in the root directory of the project.

# Code Style Guide

We will run the `.github/workflows` before merging your PR to ensure that your code is up to standard. Be sure to run the scripts in there before submitting a PR.

For type checking:

```bash
just typecheck # Check out the justfile to see the command this runs
```

For code formatting: 

```bash
just format # Check out the justfile to see the command this runs
```

## Where do you get the `typecheck` and `format` command?

You can see in `justfile` a list of scripts one can run. To see them all you can run simply `just`

# Thank you!

Thank you for wanting to participate in titanoboa and gaboon!