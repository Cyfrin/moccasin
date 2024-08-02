import subprocess
import time
import signal
import atexit

ANVIL_URL = "http://127.0.0.1:8545"


class AnvilProcess:
    def __init__(self, anvil_path="anvil", args=None):
        self.anvil_path = anvil_path
        self.args = args or []
        self.process = None

    def __enter__(self):
        self.process = subprocess.Popen(
            [self.anvil_path] + self.args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_IGN),
        )
        atexit.register(self.terminate)
        time.sleep(2)  # Give anvil some time to start up
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.terminate()

    def terminate(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
        atexit.unregister(self.terminate)

    @property
    def pid(self):
        return self.process.pid if self.process else None
