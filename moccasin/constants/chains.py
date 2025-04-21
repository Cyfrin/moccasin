from typing import Any

MAINNET = "mainnet"
SEPOLIA = "sepolia"
GOERLI = "goerli"
ARBITRUM = "arbitrum"
OPTIMISM_MAIN = "optimism-main"
OPTIMISM_TEST = "optimism-test"
POLYGON_MAIN = "polygon-main"
GNOSIS_MAIN = "gnosis-main"
GNOSIS_TEST = "gnosis-test"
BASE_MAIN = "base-main"
SYSCOIN = "syscoin"
ETHEREUMCLASSIC = "ethereumclassic"
NOVA_NETWORK = "nova-network"
VELAS = "velas"
THUNDERCORE = "thundercore"
FUSE = "fuse"
HECO = "heco"
SHIMMER_EVM = "shimmer_evm"
MANTA = "manta"
ENERGYWEB = "energyweb"
OASYS = "oasys"
OMAX = "omax"
FILECOIN = "filecoin"
KUCOIN = "kucoin"
ZKSYNC_ERA = "zksync-era"
SEPOLIA_ZKSYNC_ERA = "sepolia-zksync-era"
SHIDEN = "shiden"
ROLLUX = "rollux"
ASTAR = "astar"
CALLISTO = "callisto"
LYRA_CHAIN = "lyra-chain"
BIFROST = "bifrost"
METIS = "metis"
POLYGON_ZKEVM = "polygon-zkevm"
CORE = "core"
LISK = "lisk"
REYA_NETWORK = "reya-network"
ONUS = "onus"
HUBBLENET = "hubblenet"
SANKO = "sanko"
DOGECHAIN = "dogechain"
MILKOMEDA = "milkomeda"
KAVA = "kava"
MANTLE = "mantle"
ZETACHAIN = "zetachain"
CELO = "celo"
OASIS = "oasis"
LINEA = "linea"
BLAST = "blast"
TAIKO = "taiko"
SCROLL = "scroll"
ZORA = "zora"
NEON = "neon"
AURORA = "aurora"

CHAIN_INFO: dict[str, dict[str, Any]] = {
    MAINNET: {
        "chain_id": 1,
        "multicall2": "0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696",
    },
    SEPOLIA: {
        "chain_id": 11155111,
        "multicall2": None,
    },
    GOERLI: {
        "chain_id": 5,
        "multicall2": "0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696",
    },
    ARBITRUM: {
        "chain_id": 42161,
        "multicall2": "0x5B5CFE992AdAC0C9D48E05854B2d91C73a003858",
    },
    OPTIMISM_MAIN: {
        "chain_id": 10,
        "multicall2": "0x2DC0E2aa608532Da689e89e237dF582B783E552C",
    },
    OPTIMISM_TEST: {
        "chain_id": 420,
        "multicall2": "0x2DC0E2aa608532Da689e89e237dF582B783E552C",
    },
    POLYGON_MAIN: {
        "chain_id": 137,
        "multicall2": "0xc8E51042792d7405184DfCa245F2d27B94D013b6",
    },
    GNOSIS_MAIN: {
        "chain_id": 100,
        "multicall2": None,
    },
    GNOSIS_TEST: {
        "chain_id": 10200,
        "multicall2": None,
    },
    BASE_MAIN: {
        "chain_id": 8453,
        "multicall2": None,
    },
    SYSCOIN: {
        "chain_id": 57,
        "multicall2": None,
    },
    ETHEREUMCLASSIC: {
        "chain_id": 61,
        "multicall2": None,
    },
    NOVA_NETWORK: {
        "chain_id": 87,
        "multicall2": None,
    },
    VELAS: {
        "chain_id": 106,
        "multicall2": None,
    },
    THUNDERCORE: {
        "chain_id": 108,
        "multicall2": None,
    },
    FUSE: {
        "chain_id": 122,
        "multicall2": None,
    },
    HECO: {
        "chain_id": 128,
        "multicall2": None,
    },
    SHIMMER_EVM: {
        "chain_id": 148,
        "multicall2": None,
    },
    MANTA: {
        "chain_id": 169,
        "multicall2": None,
    },
    ENERGYWEB: {
        "chain_id": 246,
        "multicall2": None,
    },
    OASYS: {
        "chain_id": 248,
        "multicall2": None,
    },
    OMAX: {
        "chain_id": 311,
        "multicall2": None,
    },
    FILECOIN: {
        "chain_id": 314,
        "multicall2": None,
    },
    KUCOIN: {
        "chain_id": 321,
        "multicall2": None,
    },
    ZKSYNC_ERA: {
        "chain_id": 324,
        "multicall2": None,
    },
    SEPOLIA_ZKSYNC_ERA: {
        "chain_id": 300,
        "multicall2": None,
    },
    SHIDEN: {
        "chain_id": 336,
        "multicall2": None,
    },
    ROLLUX: {
        "chain_id": 570,
        "multicall2": None,
    },
    ASTAR: {
        "chain_id": 592,
        "multicall2": None,
    },
    CALLISTO: {
        "chain_id": 820,
        "multicall2": None,
    },
    LYRA_CHAIN: {
        "chain_id": 957,
        "multicall2": None,
    },
    BIFROST: {
        "chain_id": 996,
        "multicall2": None,
    },
    METIS: {
        "chain_id": 1088,
        "multicall2": None,
    },
    POLYGON_ZKEVM: {
        "chain_id": 1101,
        "multicall2": None,
    },
    CORE: {
        "chain_id": 1116,
        "multicall2": None,
    },
    LISK: {
        "chain_id": 1135,
        "multicall2": None,
    },
    REYA_NETWORK: {
        "chain_id": 1729,
        "multicall2": None,
    },
    ONUS: {
        "chain_id": 1975,
        "multicall2": None,
    },
    HUBBLENET: {
        "chain_id": 1992,
        "multicall2": None,
    },
    SANKO: {
        "chain_id": 1996,
        "multicall2": None,
    },
    DOGECHAIN: {
        "chain_id": 2000,
        "multicall2": None,
    },
    MILKOMEDA: {
        "chain_id": 2001,
        "multicall2": None,
    },
    KAVA: {
        "chain_id": 2222,
        "multicall2": None,
    },
    MANTLE: {
        "chain_id": 5000,
        "multicall2": None,
    },
    ZETACHAIN: {
        "chain_id": 7000,
        "multicall2": None,
    },
    CELO: {
        "chain_id": 42220,
        "multicall2": None,
    },
    OASIS: {
        "chain_id": 42262,
        "multicall2": None,
    },
    LINEA: {
        "chain_id": 59144,
        "multicall2": None,
    },
    BLAST: {
        "chain_id": 81457,
        "multicall2": None,
    },
    TAIKO: {
        "chain_id": 167000,
        "multicall2": None,
    },
    SCROLL: {
        "chain_id": 534352,
        "multicall2": None,
    },
    ZORA: {
        "chain_id": 7777777,
        "multicall2": None,
    },
    NEON: {
        "chain_id": 245022934,
        "multicall2": None,
    },
    AURORA: {
        "chain_id": 1313161554,
        "multicall2": None,
    },
}

BLOCKSCOUT_EXPLORERS = {
    MAINNET: "https://eth.blockscout.com/",
    SEPOLIA: "https://eth-sepolia.blockscout.com/",
    GOERLI: "https://eth-goerli.blockscout.com/",
    ARBITRUM: "https://arbitrum.blockscout.com/",
    OPTIMISM_MAIN: "https://optimism.blockscout.com/",
    OPTIMISM_TEST: "https://optimism-sepolia.blockscout.com/",
    POLYGON_MAIN: "https://polygon.blockscout.com/",
    GNOSIS_MAIN: "https://gnosis.blockscout.com/",
    GNOSIS_TEST: "https://gnosis-chiado.blockscout.com/",
    BASE_MAIN: "https://base.blockscout.com/",
    SYSCOIN: "https://explorer.syscoin.org/",
    ETHEREUMCLASSIC: "https://etc.blockscout.com/",
    NOVA_NETWORK: "https://explorer.novanetwork.io/",
    VELAS: "https://evmexplorer.velas.com/",
    THUNDERCORE: "https://explorer-mainnet.thundercore.com/",
    FUSE: "https://explorer.fuse.io/",
    SHIMMER_EVM: "https://explorer.evm.shimmer.network/",
    MANTA: "https://pacific-explorer.manta.network/",
    ENERGYWEB: "https://explorer.energyweb.org/",
    OASYS: "https://explorer.oasys.games/",
    FILECOIN: "https://filecoin.blockscout.com/",
    SHIDEN: "https://shiden.blockscout.com/",
    ROLLUX: "https://explorer.rollux.com/",
    ASTAR: "https://astar.blockscout.com/",
    CALLISTO: "https://explorer.callisto.network/",
    LYRA_CHAIN: "https://explorer.lyra.finance/",
    BIFROST: "https://explorer.mainnet.bifrostnetwork.com/",
    METIS: "https://andromeda-explorer.metis.io/",
    POLYGON_ZKEVM: "https://zkevm.blockscout.com/",
    LISK: "https://blockscout.lisk.com/",
    REYA_NETWORK: "https://explorer.reya.network/",
    ONUS: "https://explorer.onuschain.io/",
    SANKO: "https://explorer.sanko.xyz/",
    DOGECHAIN: "https://explorer.dogechain.dog/",
    MILKOMEDA: "https://explorer-mainnet-cardano-evm.c1.milkomeda.com/",
    KAVA: "https://testnet.kavascan.com/",
    MANTLE: "https://explorer.mantle.xyz/",
    ZETACHAIN: "https://zetachain.blockscout.com/",
    CELO: "https://explorer.celo.org/mainnet/",
    OASIS: "https://explorer.emerald.oasis.dev/",
    LINEA: "https://explorer.linea.build/",
    BLAST: "https://blast.blockscout.com/",
    TAIKO: "https://blockscoutapi.mainnet.taiko.xyz/",
    SCROLL: "https://blockscout.scroll.io/",
    ZORA: "https://explorer.zora.energy/",
    NEON: "https://neon.blockscout.com/",
    AURORA: "https://explorer.mainnet.aurora.dev/",
}

ZKSYNC_EXPLORERS = {
    ZKSYNC_ERA: "https://zksync2-mainnet-explorer.zksync.io",
    SEPOLIA_ZKSYNC_ERA: "https://explorer.sepolia.era.zksync.dev",
}

ETHERSCAN_EXPLORERS = {
    MAINNET: "https://api.etherscan.io/api",
    SEPOLIA: "https://api-sepolia.etherscan.io/api",
    GOERLI: "https://api-goerli.etherscan.io/api",
    ARBITRUM: "https://api.arbiscan.io/api",
    OPTIMISM_MAIN: "https://api-optimistic.etherscan.io/api",
    OPTIMISM_TEST: "https://api-goerli-optimism.etherscan.io/api",
    POLYGON_MAIN: "https://api.polygonscan.com/api",
    GNOSIS_MAIN: "https://api.gnosisscan.io/api",
    BASE_MAIN: "https://api.basescan.org/api",
    NOVA_NETWORK: "https://api-nova.arbiscan.io/api",
    POLYGON_ZKEVM: "https://api-zkevm.polygonscan.com/api",
    CORE: "https://api.scan.coredao.org/api",
    CELO: "https://api.celoscan.io/api",
    LINEA: "https://api.lineascan.build/api",
    BLAST: "https://api.blastscan.io/api",
    TAIKO: "https://api.taikoscan.io/api",
    SCROLL: "https://api.scrollscan.com/api",
    AURORA: "https://api.aurorascan.dev/api",
}

CHAIN_ID_TO_NAME = {info["chain_id"]: name for name, info in CHAIN_INFO.items()}
