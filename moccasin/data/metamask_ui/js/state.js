// Manages global application state.

let currentAccount = null;
let isMetaMaskConnected = false;
let boaNetworkDetails = {}; // Details of the active network for Boa (chainId, rpcUrl, networkName)
let isDisconnecting = false;

export const state = {
  get currentAccount() {
    return currentAccount;
  },
  set currentAccount(account) {
    currentAccount = account;
  },

  get isMetaMaskConnected() {
    return isMetaMaskConnected;
  },
  set isMetaMaskConnected(connected) {
    isMetaMaskConnected = connected;
  },

  get boaNetworkDetails() {
    return boaNetworkDetails;
  },
  set boaNetworkDetails(details) {
    boaNetworkDetails = details;
  },

  get isDisconnecting() {
    return isDisconnecting;
  },
  set isDisconnecting(val) {
    isDisconnecting = val;
  },
};
