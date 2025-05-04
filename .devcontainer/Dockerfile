# Base debian build (latest).
FROM mcr.microsoft.com/vscode/devcontainers/base:debian

# Update packages.
RUN apt-get update && apt-get install -y tar

# Set the default shell to zsh
ENV SHELL=/usr/bin/zsh

# Running everything under zsh
SHELL ["/usr/bin/zsh", "-c"]

# Dropping privileges
USER vscode

# Install rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && source $HOME/.cargo/env

# Install uv and add to PATH
# See https://docs.astral.sh/uv/guides/integration/docker/
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV PATH="/home/vscode/.local/bin:$PATH"

# Add cargo and uv to shell configuration
RUN echo 'export PATH="/home/vscode/.cargo/bin:$PATH"' >> ~/.zshrc

# Install just via uv
RUN uv tool install rust-just 

# Foundry framework
RUN curl -L https://foundry.paradigm.xyz | zsh
RUN foundryup

# Install anvil-zksync
ENV ANVIL_ZKSYNC_VERSION=0.6.0
RUN ARCH=$(dpkg --print-architecture) && \
    case $ARCH in \
    amd64) ARCH_TYPE=x86_64 ;; \
    arm64) ARCH_TYPE=aarch64 ;; \
    *) echo "Unsupported architecture: $ARCH" && exit 1 ;; \
    esac && \
    curl -L https://github.com/matter-labs/anvil-zksync/releases/download/v${ANVIL_ZKSYNC_VERSION}/anvil-zksync-v${ANVIL_ZKSYNC_VERSION}-${ARCH_TYPE}-unknown-linux-gnu.tar.gz -o $HOME/anvil-zksync.tar.gz && \
    tar xf $HOME/anvil-zksync.tar.gz -C $HOME/.foundry/bin/ && \
    chmod +x $HOME/.foundry/bin/anvil-zksync && \
    rm $HOME/anvil-zksync.tar.gz

# Install zkvyper
ENV ZKVYPER_VERSION=1.5.10
RUN ARCH=$(dpkg --print-architecture) && \
    curl -L https://github.com/matter-labs/era-compiler-vyper/releases/download/${ZKVYPER_VERSION}/zkvyper-linux-${ARCH}-gnu-v${ZKVYPER_VERSION} -o $HOME/zkvyper && \
    chmod +x $HOME/zkvyper && \
    sudo mv $HOME/zkvyper /usr/local/bin/zkvyper

# Clean up
RUN sudo apt-get autoremove -y && sudo apt-get clean -y