import atexit
import signal
import subprocess
import time

import requests
from requests import RequestException

ANVIL_URL = "http://127.0.0.1:{}"


class AnvilProcess:
    def __init__(self, anvil_path="anvil", port=8545, args=None):
        self.anvil_path = anvil_path
        self.args = args or []
        self.process = None
        self.port = port

    def __enter__(self):
        self.process = subprocess.Popen(
            [self.anvil_path] + self.args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_IGN),
        )
        atexit.register(self.terminate)
        if not self._wait_for_anvil():
            raise RuntimeError("Anvil process failed to start")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.terminate()

    def _wait_for_anvil(self, timeout=10, interval=0.5):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.post(
                    ANVIL_URL.format(self.port),
                    json={
                        "jsonrpc": "2.0",
                        "method": "eth_chainId",
                        "params": [],
                        "id": 1,
                    },
                    timeout=1,
                )
                if response.status_code == 200:
                    return True
            except RequestException:
                pass
            time.sleep(interval)
        raise RuntimeError("Anvil process failed to start in time")

    def terminate(self):
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
        atexit.unregister(self.terminate)

    @property
    def pid(self):
        return self.process.pid if self.process else None
